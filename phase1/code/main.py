import os
import argparse
import copy


# memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.
MemSize = 1000
SS_Cycles = 0
FS_Cycles = 0


class InsMem(object):

    def __init__(self, name, ioDir):
        self.id = name
        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        # read instruction memory
        byteString = self.IMem[ReadAddress:ReadAddress+4]
        instr = ''.join(byteString)

        return instr
        # # return 32 bit hex val
        # decimalNum = int(instr, base=2)
        # instr_hex = hex(decimalNum)
        # return instr_hex  
          

class DataMem(object):

    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
            self.DMem = self.DMem + ['0'*8]*(MemSize - len(self.DMem))
            # print(len(self.DMem))

    def readInstr(self, ReadAddress):
        # read data memory
        byteString = self.DMem[ReadAddress:ReadAddress+4]
        data = ''.join(byteString)

        return data
        # # return 32 bit hex val
        # decimalNum = int(data, base=2)
        # data_hex = hex(decimalNum)
        # return data_hex
        
    # WriteAddress: integer
    # WriteData: 32-bit binary string
    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
        self.DMem[Address:Address+4] = [WriteData[i:i+8] for i in range(0, len(WriteData), 8)]
        # self.DMem[Address:Address+4] = [WriteData[i:i+8] for i in range(0, len(WriteData), 2)]
                     
    def outputDataMem(self):
        resPath = self.ioDir + "/" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])


class RegisterFile(object):

    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = ['0'*32 for i in range(32)]  # 32 registers with initial value
    
    def readRF(self, Reg_addr):
        # Fill in
        # No exception handling now!
        return self.Registers[Reg_addr]
    
    # Reg_addr: integer
    # Wrt_reg_data: 32-bit binary string
    def writeRF(self, Reg_addr, Wrt_reg_data):
        # Fill in
        # No exception handling now!
        self.Registers[Reg_addr] = Wrt_reg_data
         
    def outputRF(self, cycle):
        op = ["-"*70+"\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        op.extend([str(val)+"\n" for val in self.Registers])
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)


class State(object):

    def __init__(self):
        # PC is the address of the instruction to be fetched
        self.IF = {"nop": False, "PC": 0}
        # Instr is 32-bit instruction coming from previous IF stage
        self.ID = {"nop": False, "Instr": 0, "PC_Plus_4": 0}

        # Read_data1, Read_data2: data from rs1, rs2
        # alu_op: ALU operation code
        # is_I_type: the instruction is I-type or not
        # Imm: immediate value after sign-extend

        # Rs, Rt: rs1, rs2. Needed to be compared with rd in MEM and WB stage for hazard detection!
        # Wrt_reg_addr: address of the register to write (rd)
        
        # rd_mem: whether to read from memory in MEM stage
        # wrt_mem: whether to write to memory in MEM stage
        # wrt_enable: whether to write to register file in WB stage
        self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0, 
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0, "jump": False, "PC_Plus_4": 0, "branch_type": 0, "PC_target": 0, "alu_ctrl": 0}
        # ALUresult: result from ALU
        # Store_data: data to be stored into data memory
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0, 
                   "wrt_mem": 0, "wrt_enable": 0}
        # Wrt_data: data to be written back to register file
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}

        # Why do we need Rs, Rt in MEM, WB stage???


class Core(object):

    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        # The computation results will be stored in latches(nextState) and update in next stage, so that we will not read the incorrect values which are just updated in the current cycle
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem

    # sign extend a binary string to a decimal number
    def signExtend(self, binaryStr):
        if binaryStr[0] == '0':
            return int(binaryStr, 2)
        else:
            return int(binaryStr, 2) - (1 << len(binaryStr))  # for a negative binary number with n bits, its decimal value = unsigned value - 2^n
    
    # convert a decimal number to a binary string with bitWidth bits
    def decimalToBinary(self, decimalNum, bitWidth):
        if decimalNum >= 0:
            binaryStr = bin(decimalNum)[2:]  # remove '0b' prefix
            return "0" * (bitWidth - len(binaryStr)) + binaryStr
        else:
            return bin((1 << bitWidth) + decimalNum)[2:]
        
    # convert an unsigned 32-bit decimal number to a signed decimal number
    def unsignedDecimalToSignedDecimal(self, unsignedNum):
        if unsignedNum >= (1 << 31):  # negative
            return unsignedNum - (1 << 32)
        else:
            return unsignedNum


class SingleStageCore(Core):

    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"

    def step(self):
        # Your implementation
        # IF, ID, EX, MEM, WB all in one stage...
        
        # IF stage
        PC = self.state.IF["PC"]
        instr = self.ext_imem.readInstr(PC)
        self.state.ID["PC_Plus_4"] = PC + 4  # jal will write new PC back into rd in WB stage
        self.nextState.IF["PC"] = self.state.ID["PC_Plus_4"]  # default PC update

        # ID stage (expception handling is needed in further implementation)
        opcode = instr[-7:]
        fun3 = instr[-15:-12]
        if opcode == '0110011':  # R-type instruction
            Rs = int(instr[-20:-15], 2)
            Rt = int(instr[-25:-20], 2)
            self.state.EX["Wrt_reg_addr"] = int(instr[-12:-7], 2)
            fun7 = instr[-32:-25]
            self.state.EX["Read_data1"] = self.signExtend(self.myRF.readRF(Rs))
            self.state.EX["Read_data2"] = self.signExtend(self.myRF.readRF(Rt))
            self.state.EX["wrt_enable"] = 1
            self.state.EX["alu_op"] = "10"
            if fun3 == "000":
                if fun7 == "0100000":  # SUB
                    self.state.EX["alu_ctrl"] = "0110"
                elif fun7 == "0000000":  # ADD
                    self.state.EX["alu_ctrl"] = "0010"
                else:
                    self.state.EX["alu_ctrl"] = 0  # default 0 for unsupported instructions (or we need exception handling)
            elif fun3 == "111":  # AND (exception handling for fun7 needed in further implementation)
                self.state.EX["alu_ctrl"] = "0000"
            elif fun3 == "110":  # OR (exception handling for fun7 needed in further implementation)
                self.state.EX["alu_ctrl"] = "0001"
            elif fun3 == "100":  # XOR (exception handling for fun7 needed in further implementation)
                self.state.EX["alu_ctrl"] = "0011"
            else:
                self.state.EX["alu_ctrl"] = 0  # default 0 for unsupported instructions (or we need exception handling)
        elif opcode == '0010011':  # I-type instruction (except lw)
            Rs = int(instr[-20:-15], 2)
            self.state.EX["Wrt_reg_addr"] = int(instr[-12:-7], 2)
            self.state.EX["Imm"] = self.signExtend(instr[-32:-20])  # Why do we need sign extend in logical operation???
            self.state.EX["is_I_type"] = True
            self.state.EX["Read_data1"] = self.signExtend(self.myRF.readRF(Rs))
            self.state.EX["wrt_enable"] = 1
            self.state.EX["alu_op"] = "10"
            if fun3 == '000':  # ADDI (exception handling for fun7 needed in further implementation)
                self.state.EX["alu_ctrl"] = "0010"
            elif fun3 == '111':  # ANDI (exception handling for fun7 needed in further implementation)
                self.state.EX["alu_ctrl"] = "0000"
            elif fun3 == '110':  # ORI (exception handling for fun7 needed in further implementation)
                self.state.EX["alu_ctrl"] = "0001"
            elif fun3 == '100':  # XORI (exception handling for fun7 needed in further implementation)
                self.state.EX["alu_ctrl"] = "0011"
            else:
                self.state.EX["alu_ctrl"] = 0  # default 0 for unsupported instructions (or we need exception handling)
        elif opcode == '1101111':  # UJ-type instruction (JAL)
            self.state.EX["Wrt_reg_addr"] = int(instr[-12:-7], 2)
            self.state.EX["Imm"] = self.signExtend(instr[0]+instr[12:20]+instr[11]+instr[1:11]+"0")
            self.state.EX["is_I_type"] = True
            self.state.EX["wrt_enable"] = 1
            self.state.EX["alu_op"] = "00"
            self.state.EX["jump"] = True
        elif opcode == '1100011':  # SB-type instruction (branch)
            Rs = int(instr[-20:-15], 2)
            Rt = int(instr[-25:-20], 2)
            self.state.EX["Imm"] = self.signExtend(instr[0]+instr[24]+instr[1:7]+instr[20:24]+"0")
            self.state.EX["is_I_type"] = True
            self.state.EX["Read_data1"] = self.signExtend(self.myRF.readRF(Rs))
            self.state.EX["Read_data2"] = self.signExtend(self.myRF.readRF(Rt))
            self.state.EX["alu_op"] = "01"
            self.state.EX["PC_target"] = PC + self.state.EX["Imm"]  # an extra adder needed here for branch target address calculation
            if fun3 == '000':  # BEQ
                self.state.EX["branch_type"] = "01"
            elif fun3 == '001':  # BNE
                self.state.EX["branch_type"] = "10"
            else:
                self.state.EX["branch_type"] = 0  # default 0 for unsupported instructions (or we need exception handling)
        elif opcode == '0000011':  # I-type instruction (load)
            Rs = int(instr[-20:-15], 2)
            self.state.EX["Wrt_reg_addr"] = int(instr[-12:-7], 2)
            self.state.EX["Imm"] = self.signExtend(instr[-32:-20])
            self.state.EX["is_I_type"] = True
            self.state.EX["Read_data1"] = self.signExtend(self.myRF.readRF(Rs))
            self.state.EX["rd_mem"] = 1
            self.state.EX["wrt_enable"] = 1
            self.state.EX["alu_op"] = "00"
        elif opcode == '0100011':  # S-type instruction (store)
            Rs = int(instr[-20:-15], 2)
            Rt = int(instr[-25:-20], 2)
            self.state.EX["Imm"] = self.signExtend(instr[-32:-25]+instr[-12:-7])
            self.state.EX["is_I_type"] = True
            self.state.EX["Read_data1"] = self.signExtend(self.myRF.readRF(Rs))
            self.state.EX["Read_data2"] = self.signExtend(self.myRF.readRF(Rt))
            self.state.EX["wrt_mem"] = 1
            self.state.EX["alu_op"] = "00"

        elif opcode == '1111111':  # halt instruction
            self.nextState.IF["nop"] = True  # halt condition
            self.nextState.IF["PC"] = PC  # keep PC unchanged
        else:
            self.nextState.IF["nop"] = True  # halt the processor if there's an unknown instruction
            # Exception handler
            pass
            return
        
        # EX stage
        self.state.EX["PC_Plus_4"] = self.state.ID["PC_Plus_4"]
        if self.state.EX["alu_op"] == "00":  
            if self.state.EX["jump"] == True:  # for JAL
                self.state.MEM["ALUresult"] = PC + self.state.EX["Imm"]  
                self.nextState.IF["PC"] = self.state.MEM["ALUresult"]  # update PC here
                self.state.MEM["ALUresult"] = self.state.EX["PC_Plus_4"]  # for writing back to rd (an mux controlled by jump signal could do this)
            elif self.state.EX["wrt_mem"] == 1:  # for store
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] + self.state.EX["Imm"]  
                self.state.MEM["store_data"] = self.decimalToBinary(self.state.EX["Read_data2"], 32)  # for store
            else:  # rd_mem == 1:  # for load
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] + self.state.EX["Imm"]  # for load
        elif self.state.EX["alu_op"] == "01":  # for branch
            self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] - self.state.EX["Read_data2"]
            if self.state.EX["branch_type"] == "01":  # BEQ
                if self.state.MEM["ALUresult"] == 0:
                    self.nextState.IF["PC"] = self.state.EX["PC_target"]  # update PC
            elif self.state.EX["branch_type"] == "10":  # BNE
                if self.state.MEM["ALUresult"] != 0:
                    self.nextState.IF["PC"] = self.state.EX["PC_target"]  # update PC
        elif self.state.EX["alu_op"] == "10":  # for R-type and part of I-type instructions
            if self.state.EX["alu_ctrl"] == "0010":  # ADD, ADDI
                if self.state.EX["is_I_type"]:
                    unsignedResult = (self.state.EX["Read_data1"] + self.state.EX["Imm"]) & 0xFFFFFFFF  # 32-bit overflow handling. The result is unsigned int.
                    self.state.MEM["ALUresult"] = self.unsignedDecimalToSignedDecimal(unsignedResult)
                else:
                    unsignedResult = (self.state.EX["Read_data1"] + self.state.EX["Read_data2"]) & 0xFFFFFFFF  # 32-bit overflow handling. The result is unsigned int.
                    self.state.MEM["ALUresult"] = self.unsignedDecimalToSignedDecimal(unsignedResult)
            elif self.state.EX["alu_ctrl"] == "0110":  # SUB
                unsignedResult = (self.state.EX["Read_data1"] - self.state.EX["Read_data2"]) & 0xFFFFFFFF  # 32-bit overflow handling. The result is unsigned int.
                self.state.MEM["ALUresult"] = self.unsignedDecimalToSignedDecimal(unsignedResult)
            elif self.state.EX["alu_ctrl"] == "0000":  # AND, ANDI
                if self.state.EX["is_I_type"]:
                    self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] & self.state.EX["Imm"]
                else:
                    self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] & self.state.EX["Read_data2"]
            elif self.state.EX["alu_ctrl"] == "0001":  # OR, ORI
                if self.state.EX["is_I_type"]:
                    self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] | self.state.EX["Imm"]
                else:
                    self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] | self.state.EX["Read_data2"]
            elif self.state.EX["alu_ctrl"] == "0011":  # XOR, XORI
                if self.state.EX["is_I_type"]:
                    self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] ^ self.state.EX["Imm"]
                else:
                    self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] ^ self.state.EX["Read_data2"]
        else:  # will not happen now
            self.state.MEM["ALUresult"] = 0  # default 0 for unsupported instructions (or we need exception handling)

        # MEM stage
        self.state.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
        self.state.MEM["rd_mem"] = self.state.EX["rd_mem"]
        self.state.MEM["wrt_mem"] = self.state.EX["wrt_mem"]
        self.state.MEM["wrt_enable"] = self.state.EX["wrt_enable"]
        if self.state.MEM["wrt_mem"] == 1:  # store
            self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"], self.state.MEM["store_data"])
        elif self.state.MEM["rd_mem"] == 1:  # load
            self.state.WB["Wrt_data"] = self.ext_dmem.readInstr(self.state.MEM["ALUresult"])
        else:
            self.state.WB["Wrt_data"] = self.decimalToBinary(self.state.MEM["ALUresult"], 32)  # for UJ-type, R-type and other I-type instructions. SB-type instructions do not have wrt_enable signal.

        # WB stage
        self.state.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
        self.state.WB["wrt_enable"] = self.state.MEM["wrt_enable"]
        if self.state.WB["wrt_enable"] == 1 and self.state.WB["Wrt_reg_addr"] != 0:  # write back to RF, but x0 is always 0
            self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], self.state.WB["Wrt_data"])

        # self.halted = True
        self.halted = False
        if self.state.IF["nop"]:
            self.halted = True
            # print(self.cycle)
            
        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ... 
            
        self.state = copy.deepcopy(self.nextState)  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

        global SS_Cycles
        SS_Cycles += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


class FiveStageCore(Core):

    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "/FS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_FS.txt"

    def step(self):
        # Your implementation

        # We also need to do five stages in one step, but each stage is for different instructions.
        # --------------------- WB stage ---------------------
        
        
        
        # --------------------- MEM stage --------------------
        
        
        
        # --------------------- EX stage ---------------------
        
        
        
        # --------------------- ID stage ---------------------
        
        
        
        # --------------------- IF stage ---------------------
        
        self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True
        
        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ... 
        
        self.state = copy.deepcopy(self.nextState)  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


if __name__ == "__main__":
     
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default=script_dir, type=str, help='Directory containing the input files.')
    # parse_args() read the args provided from the user in commmand line
    args = parser.parse_args()  

    # if iodir uses default value, we will get the absolute path of the default work directory
    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)
    
    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        if not ssCore.halted:
            ssCore.step()
        
        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()

    # print(SS_Cycles)
    InstructionCount = SS_Cycles - 1
    SS_CPI = SS_Cycles / InstructionCount
    SS_IPC = InstructionCount / SS_Cycles

    op = [
        "Performance of Single Stage:\n",
        f"#Cycles -> {SS_Cycles}\n",
        f"#Instructions -> {InstructionCount}\n",
        f"CPI -> {SS_CPI}\n",
        f"IPC -> {SS_IPC}\n",
        # "\n",
        # "Performance of Five Stage:\n",
        # f"#Cycles -> {fs_data['cycles']}\n",
        # f"#Instructions -> {fs_data['instructions']}\n",
        # f"CPI -> {fs_data['cpi']}\n",
        # f"IPC -> {fs_data['ipc']}\n"
    ]
    resPath = os.path.join(ioDir, "PerformanceMetrics.txt")
    with open(resPath, "w") as file:
        file.writelines(op)
