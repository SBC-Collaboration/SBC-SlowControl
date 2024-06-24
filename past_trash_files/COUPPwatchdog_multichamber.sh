#!/bin/bash
#
# NOTE:  this is a bash script.  syntax is slightly different from tcsh
#
# 20100527 v1.0 - queries mysql and sends mail

# exit 0

DEBUGGING=false
DEBUGGING=true

WATCHDOG_DIR=~
WATCHDOG_DIR="${WATCHDOG_DIR}/COUPPwatchdog"

CHAMBER_LIST="$(find ${WATCHDOG_DIR} -mindepth 1 -maxdepth 1 -type d)"

if $DEBUGGING
then
    echo "${CHAMBER_LIST}"
    echo
fi


for CHAMBER_DIR in $CHAMBER_LIST
do

    if $DEBUGGING
    then
        echo $CHAMBER_DIR
        echo
    fi

    CHAMBER_NAME="${CHAMBER_DIR##*/}"

    ACTIVE_FILE="${CHAMBER_DIR}/watchdog_on"
    if [ -e "${ACTIVE_FILE}" ]
    then

        HOST_FILE="${CHAMBER_DIR}/alarm_host.txt";
        if [ -s "${HOST_FILE}" ]
        then
            MYSQL_HOST="$(cat ${HOST_FILE} | head -n 1)"
        else
            MYSQL_HOST="coupp@coupp2ls2.snolab.ca"
        fi

        DB_FILE="${CHAMBER_DIR}/alarm_database.txt";
        if [ -s "${DB_FILE}" ]
        then
            ALARM_TABLE="$(cat ${DB_FILE} | head -n 1)"
        else
            ALARM_TABLE="pico2l_DAQ_alarms"
        fi

        # ssh $MYSQL_HOST -L 3307:127.0.0.1:3306 -N &
        # SSH_PID=$!

        ############################
        # read in e-mail addresses #
        ############################
        EMAIL_FILE="${CHAMBER_DIR}/alarm_email_list.txt"
        if [ -s "${EMAIL_FILE}" ]
        then
            EMAIL_LIST="$(cat ${EMAIL_FILE})"
            NO_EMAIL_LIST=false
        else
            EMAIL_LIST="pico_alarm@snolab.ca"
            NO_EMAIL_LIST=true
        fi

        ADMIN_FILE="${CHAMBER_DIR}/alarm_admin_list.txt"
        if [ -s "${ADMIN_FILE}" ]
        then
            ADMIN_LIST="$(cat ${ADMIN_FILE})"
            NO_ADMIN_LIST=false
        else
            ADMIN_LIST="pico_alarm@snolab.ca"
            NO_ADMIN_LIST=true
        fi

        ############################
        # check current alarm file #
        ############################

        ALARM_FILE="${CHAMBER_DIR}/last_alarm_sent.txt"
        if [ -s "${ALARM_FILE}" ]
        then
            LAST_ALARM_TYPE=$(cat "${ALARM_FILE}" | head -n 1)
            LAST_ALARM_DATIME=$(cat "${ALARM_FILE}" | head -n 2 | tail -n 1)
            LAST_ADMIN_DATIME=$(cat "${ALARM_FILE}" | head -n 3 | tail -n 1)
            LAST_ALARM_LENGTH=$(cat "${ALARM_FILE}" | head -n 4 | tail -n 1)
        else
            LAST_ALARM_TYPE=NONE
            LAST_ALARM_DATIME=0
            LAST_ADMIN_DATIME=0
            LAST_ALARM_LENGTH=0
        fi

        if $DEBUGGING
        then
            echo "${ALARM_FILE}"
            echo "last_alarm_type = ${LAST_ALARM_TYPE}"
            echo "last_alarm_datime = ${LAST_ALARM_DATIME}"
            echo "last_admin_datime = ${LAST_ADMIN_DATIME}"
            echo
        fi

        ############################
        # get current alarm status #
        ############################

        QUERY="use coupp_alarms; select datime from ${ALARM_TABLE} where id=1; select alarm_state from ${ALARM_TABLE} where id=1; select alarm_message from ${ALARM_TABLE} where id=1"

        SSH_COMMAND="echo \"${QUERY}\" | mysql --user=coupp_watchdog"

        QUERY_RESULT="$(echo "${SSH_COMMAND}" | ssh "${MYSQL_HOST}")"

        QUERY_RESULT=$(echo "${QUERY_RESULT}" | tail -n 6)

        QUERY_LENGTH=$(echo "${QUERY_RESULT}" | wc -l)

        DATIME=$(echo "${QUERY_RESULT}" | head -n 2 | tail -n 1)
        ALARM_STATE=$(echo "${QUERY_RESULT}" | head -n 4 | tail -n 1)
        ALARM_MESSAGE=$(echo "${QUERY_RESULT}" | head -n 6 | tail -n 1)
        ALARM_MESSAGE_LENGTH=${#ALARM_MESSAGE}

        QUERY_SUCCESS=false

        if [ -n "${DATIME}" ] && [ -n "${ALARM_STATE}" ] && [ -n "${ALARM_MESSAGE}" ] && [ "${QUERY_LENGTH}" -eq 6 ]
        then
            QUERY_SUCCESS=true
        fi

        if $DEBUGGING
        then
            echo "${QUERY_RESULT}"
            echo
            echo "datime = ${DATIME}"
            echo "alarm_state = ${ALARM_STATE}"
            echo "alarm_message = ${ALARM_MESSAGE}"
            echo "query_length = ${QUERY_LENGTH}"
            echo "query_success = ${QUERY_SUCCESS}"
            if $QUERY_SUCCESS
            then
                echo "Query successful"
            else
                echo "Query NOT successful"
            fi
            echo
        fi

        ##########################
        # get current alarm type #
        ##########################

        DATIME_NOW=$(date +%s)

        if $QUERY_SUCCESS
        then
            let QUERY_AGE=$DATIME_NOW-$DATIME
        else
            QUERY_AGE=0
        fi

        if $DEBUGGING
        then
            echo "query result is ${QUERY_AGE} seconds old"
            echo
        fi

        ####################################
        # determine the current alarm type #
        ####################################

        if $QUERY_SUCCESS
        then
            if [ $ALARM_STATE = "ALARM" ]
            then
                ALARM_TYPE=ALARM
                QUERY_AGE_LIMIT=300
            elif [ $ALARM_STATE = "OK" ]
            then
                ALARM_TYPE=ON
                QUERY_AGE_LIMIT=300
            elif [ $ALARM_STATE = "OFF" ]
            then
                ALARM_TYPE=OFF
                QUERY_AGE_LIMIT=0
            else
                ALARM_TYPE=HUH
                QUERY_AGE_LIMIT=300
            fi
            if [ $QUERY_AGE -gt $QUERY_AGE_LIMIT ] && [ $QUERY_AGE_LIMIT -gt 0 ]
            then
                ALARM_TYPE=STALE
            fi
        else
            ALARM_TYPE=LOST
        fi

        if $DEBUGGING
        then
            echo "alarm_type is ${ALARM_TYPE}"
            echo
        fi

        #################################
        # determine what alarms to send #
        #################################

        let ALARM_AGE=$DATIME_NOW-$LAST_ALARM_DATIME
        let ADMIN_AGE=$DATIME_NOW-$LAST_ADMIN_DATIME

        case $ALARM_TYPE in
            ON)
                ALARM_REFRESH=0 # never
                ADMIN_REFRESH=86400 # once a day
                ALARM_SUBJECT="active"
                ALARM_MESSAGE="PICOwatchdog is active from this computer.  All is well.
        ${ALARM_MESSAGE}"
            ;;
            OFF)
                ALARM_REFRESH=0 # never
                ADMIN_REFRESH=5184000 # once every other month
                ALARM_SUBJECT="inactive"
                ALARM_MESSAGE="PICOwatchdog is inactive on this computer.  You will not receive any alarms.
        ${ALARM_MESSAGE}"
            ;;
            ALARM)
                ALARM_REFRESH=3600 # once an hour
                ADMIN_REFRES=3600 # once an hour
                ALARM_SUBJECT="ALARM!!!"
                ALARM_MESSAGE="PICOwatchdog detects an ALARM!!!
        ${ALARM_MESSAGE}"
            ;;
            HUH)
                ALARM_REFRESH=86400 # once a day
                ADMIN_REFRESH=7200 # once every other hour
                ALARM_SUBJECT="unknown status"
                ALARM_MESSAGE="PICOwatchdog detects unknown mySQL status
        ${ALARM_MESSAGE}"
            ;;
            STALE)
                ALARM_REFRESH=86400 # once a day
                ADMIN_REFRESH=7200 # once every other hour
                ALARM_SUBJECT="stale data"
                ALARM_MESSAGE="PICOwatchdog received stale data from mySQL
        ${ALARM_MESSAGE}"
            ;;
            LOST)
                ALARM_REFRESH=0 # never
                ADMIN_REFRESH=7200 # once every other hour
                ALARM_SUBJECT="lost connection"
                ALARM_MESSAGE="PICOwatchdog cannot connect to the mySQL database"
            ;;
            *)
                ALARM_REFRESH=86400 # once a day
                ADMIN_REFRESH=7200 # once every other hour
                ALARM_SUBJECT="BASH error"
                ALARM_MESSAGE="PICOwatchdog.sh has a bug"
            ;;
        esac

        ALARM_MESSAGE="PICOwatchdog:  ${CHAMBER_NAME}

        ${ALARM_MESSAGE}

        Shifter to follow alarm response protocol.  An e-mail will be sent to pico_alarm@snolab.ca when the alarm is being dealt with."

        ALARM_SUBJECT="PICOwatchdog ${CHAMBER_NAME}:  ${ALARM_SUBJECT}"

        if $DEBUGGING
        then
            echo "alarm_age ${ALARM_AGE} >? ${ALARM_REFRESH}"
            echo "admin_age ${ADMIN_AGE} >? ${ADMIN_REFRESH}"
            echo
        fi

        SEND_EMAIL=false
        if [ $ALARM_TYPE != $LAST_ALARM_TYPE ]
        then
            DATIME_ALARM=$DATIME_NOW
            DATIME_ADMIN=$DATIME_NOW
            if [ $ALARM_REFRESH -gt 0 ]
            then
                SEND_LIST="${EMAIL_LIST}"
                SEND_EMAIL=true
                if $NO_EMAIL_LIST
                then
                    ALARM_SUBJECT="${ALARM_SUBJECT} (No E-mail list, default send only!!!)"
                fi
            elif [ $ADMIN_REFRESH -gt 0 ]
            then
                SEND_LIST="${ADMIN_LIST}"
                SEND_EMAIL=true
                if $NO_ADMIN_LIST
                then
                    ALARM_SUBJECT="${ALARM_SUBJECT} (No Admin E-mail list, default send only!!!)"
                fi
            fi
        elif [ $ALARM_MESSAGE_LENGTH != $LAST_ALARM_LENGTH ] && [ $ALARM_STATE = "ALARM" ]
        then
            DATIME_ALARM=$DATIME_NOW
            DATIME_ADMIN=$DATIME_NOW
            if [ $ALARM_REFRESH -gt 0 ]
            then
                SEND_LIST="${EMAIL_LIST}"
                SEND_EMAIL=true
                if $NO_EMAIL_LIST
                then
                    ALARM_SUBJECT="${ALARM_SUBJECT} (No E-mail list, default send only!!!)"
                fi
            elif [ $ADMIN_REFRESH -gt 0 ]
            then
                SEND_LIST="${ADMIN_LIST}"
                SEND_EMAIL=true
                if $NO_ADMIN_LIST
                then
                    ALARM_SUBJECT="${ALARM_SUBJECT} (No Admin E-mail list, default send only!!!)"
                fi
            fi
        else
            DATIME_ALARM=$LAST_ALARM_DATIME
            DATIME_ADMIN=$DATIME_NOW
            if [ $ALARM_AGE -gt $ALARM_REFRESH ] && [ $ALARM_REFRESH -gt 0 ]
            then
                SEND_LIST="${EMAIL_LIST}"
                SEND_EMAIL=true
                DATIME_ALARM=$DATIME_NOW
                if $NO_EMAIL_LIST
                then
                    ALARM_SUBJECT="${ALARM_SUBJECT} (No E-mail list, default send only!!!)"
                fi
            elif [ $ADMIN_AGE -gt $ADMIN_REFRESH ] && [ $ADMIN_REFRESH -gt 0 ]
            then
                SEND_LIST="${ADMIN_LIST}"
                SEND_EMAIL=true
                if $NO_ADMIN_LIST
                then
                    ALARM_SUBJECT="${ALARM_SUBJECT} (No Admin E-mail list, default send only!!!)"
                fi
            fi
        fi

        ######################
        # exit if we're done #
        ######################

        if $SEND_EMAIL
        then
            if $DEBUGGING
            then
                echo "E-mail to send!"
                echo
            fi

            ###############
            # send alarms #
            ###############

            for EMAIL_ADDRESS in $SEND_LIST
            do
                if [ -n "${EMAIL_ADDRESS}" ]
                then
                    echo "${ALARM_MESSAGE}" | mail -s "${ALARM_SUBJECT}" "${EMAIL_ADDRESS}"
                    if $DEBUGGING
                    then
                        echo "Sent mail to ${EMAIL_ADDRESS} Re: ${ALARM_SUBJECT}:  ${ALARM_MESSAGE}"
                        echo
                    fi
                else
                    if $DEBUGGING
                    then
                        echo "Got an empty e-mail address!"
                        echo
                    fi
                fi
            done

            #########################
            # record new last alarm #
            #########################

            echo "${ALARM_TYPE}" > "${ALARM_FILE}"
            echo "${DATIME_ALARM}" >> "${ALARM_FILE}"
            echo "${DATIME_ADMIN}" >> "${ALARM_FILE}"
            echo "${ALARM_MESSAGE_LENGTH}" >> "${ALARM_FILE}"
            echo "To: ${SEND_LIST}" >> "${ALARM_FILE}"
            echo "Re: ${ALARM_SUBJECT}" >> "${ALARM_FILE}"
            echo "${ALARM_MESSAGE}" >> "${ALARM_FILE}"

            # kill $SSH_PID

        else
            if $DEBUGGING
            then
                echo "No e-mail to send!"
                echo
            fi
        fi

    fi

done

exit 0

