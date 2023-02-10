def read_GVL(filename, beginrow, finalrow):

    file = open(str(filename),'r')
    produce_address_dic={}
    base_address=12288

    lines=file.readlines()
    for i in range(beginrow-1,finalrow):
        line_list=lines[i].split()
        # print(int(''.join(filter(str.isdigit, line_list[2]))))
        try:
            produce_address_dic[line_list[0]] = int(int(''.join(filter(str.isdigit, line_list[2])))/2+base_address)

        except:
            pass

    return produce_address_dic

if __name__ == "__main__":
    print(read_GVL("D:\\PythoProjects\\SBCslowcontrol\\SBC-SlowControl\\MB_TcGVL_v1.txt",201,213))
    # print(read_GVL("D:\\GIthub\\runze\\SBC_linux\\SBC-SlowControl\\MB_TcGVL.txt", 7, 32))

