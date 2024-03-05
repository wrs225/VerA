from vera.vparser.parser import parse
from vera.vparser.ast import Instance, Node, Ioport, Real, Decl, Assign, Output, Input
from vera.vparser.codegen import ASTCodeGenerator

class AMSFileLinker():

    #Must be a list of RTL Blocks!
    def __init__(self, top_filename, preprocess_include_ams = [], preprocess_include_v = [], rel_prec = 0.01):
        self.top_filename = top_filename
        self.module = None
        self.params = {}
        self.ports = {}
        self.wires = {}
        self.assigns = {}
        self.instances = {}
        self.includes = {}
        self.include_v = preprocess_include_v
        self.include_ams = []
        self.ast = None

        with open(self.top_filename) as f:
            self.file = f.read()
        
        for rtl_block in preprocess_include_ams:
            rtl_block.generate_verilog_src("./")

            self.include_ams.append(rtl_block.name + ".v")


        ast, directives = parse(self.file)
        ast.show()
        self.ast = ast



        for i in AMSFileLinker._get_instance_list(ast):
            self.instances[i.name] = i

        for d in directives:
            if "include" in d[1]:
                filename = d[1].split('"')[1::2][0]
                with open('./' + filename) as f:
                    self.includes[filename] = {}
                    self.includes[filename]["parsedfile"] = parse(f.read())
                    if "./" in filename:
                        self.includes[filename]["instances"] = AMSFileLinker._get_instance_list(self.includes[filename]["parsedfile"])
                    else:
                        self.includes[filename]["instances"] = AMSFileLinker._get_instance_list(self.includes["./" + filename]["parsedfile"])
                    
        

    def link(self):
        #Get bitwidth mapping from all instantiated modules
        fillable_real_instances = AMSFileLinker._get_unfilled_real_instances(self.ast)
        #take fillable real instances and just return an array of strings representing all declared vars
        undecld_vars = {}
        for i in fillable_real_instances:
            if(isinstance(i, Ioport)):
                undecld_vars[i.second.name] = i
            elif(isinstance(i,Decl)):
                for d in i.list:
                    undecld_vars[d.name[0]] = i



        if(len(undecld_vars.keys()) != len(set(undecld_vars.keys()))):
            raise Exception("Duplicate variable names in AMS module")
        
    
        
        declared_module_instances = AMSFileLinker._get_instance_list(self.ast)
        print(declared_module_instances[0].show())
        declared_forward_assignments = AMSFileLinker._get_assign_dict(self.ast)
        declared_backward_assignments = AMSFileLinker._get_backwards_assign_dict(self.ast)

        declared_module_assgns_output = {}
        declared_module_assgns_input = {}

        for declared_module in declared_module_instances:
            
            print(self.includes.keys())
            print(declared_module.module + ".v" in self.includes.keys())
            print(type(list(self.includes.keys())[2]))
            print(type(declared_module.module + ".v"))
            print(declared_module.module + ".v" == list(self.includes.keys())[2])
            if not "./" in declared_module.module + ".v":
                declared_module.module = "./" + declared_module.module
            module_interface = self.includes[declared_module.module + ".v"]["parsedfile"][0]

            module_ports = AMSFileLinker._obtain_port_bitwidths(module_interface)

            declared_module_unassgns = list(filter(lambda x: x.argname == None, declared_module.portlist))
            if(len(declared_module_unassgns) > 0):
                print("[WARN] " + str(list(map(lambda x: x.portname, declared_module_unassgns))) + " never assigned to values")
            declared_module_assgns_output = dict(map(lambda x: ( str(x.first.name), x.first.width), filter(lambda x: isinstance(x.first,Output), module_ports)))
            declared_module_assgns_input = dict(map(lambda x: ( str(x.first.name), x.first.width), filter(lambda x: isinstance(x.first,Input), module_ports)))

            

                

            for port in declared_module.portlist:


                assert port.portname in declared_module_assgns_output.keys() or port.portname in declared_module_assgns_input.keys(), "Port " + port.portname + " not found in module " + declared_module.module + " interface."
                

                if port.portname in declared_module_assgns_output.keys():
                    print(port.portname)
                    print(port.argname)
                    declared_module_assgns_output[str(port.argname)] = declared_module_assgns_output[port.portname]
                    #delete entry portname from declared_module_assgns_output
                    del declared_module_assgns_output[str(port.portname)]


                if port.portname in declared_module_assgns_input.keys():
                    declared_module_assgns_input[str(port.argname)] = declared_module_assgns_input[port.portname]
                    #delete entry portname from declared_module_assgns_output
                    del declared_module_assgns_input[str(port.portname)]




            self.instances[declared_module.name[0]] = (declared_module_assgns_input, declared_module_assgns_output)
            


        for undcl_var_name, info in undecld_vars.items():

            
            #check if info isisntance Ioport

            identical_port_list = []
            port_path = undcl_var_name
            if(isinstance(info,Ioport)):

                if isinstance(info.first,Output):
                    while port_path in declared_forward_assignments.keys():
                        port_path = declared_forward_assignments[port_path]
                        #remove the declared_forward_assignment port from the list of undecld_vars
                        identical_port_list.append(port_path)

                    print(identical_port_list)
                    print(port_path)
                    print(type(list(declared_module_assgns_output.keys())[0]))
                    print(list(declared_module_assgns_output.keys()))
                    for i in identical_port_list:
                        print(declared_module_assgns_output.items())
                        AMSFileLinker._replace_port_type_by_name(self.ast, undcl_var_name, declared_module_assgns_output[port_path])
                else:
                    #same for this else but with declared_backward_assignments

                    while port_path in declared_backward_assignments.keys():
                        port_path = declared_backward_assignments[port_path]
                        identical_port_list.append(port_path)

                    print(identical_port_list)
                    print(port_path)
                    for i in identical_port_list + [port_path] + [undcl_var_name]:
                        AMSFileLinker._replace_port_type_by_name(self.ast, undcl_var_name, declared_module_assgns_input[port_path])

        codegen = ASTCodeGenerator()
        self.ast.show()
        rslt = codegen.visit(self.ast)
        print(rslt)
        with open("test.v", "w") as f:
            f.write(rslt)


            
        #for each declared var, we need to find the corresponding bitwidth in the instantiated module


    def _replace_port_type_by_name(tree, name, bitsobject):
        if(not isinstance(tree, Node)):
            return tree
        if(isinstance(tree, Ioport)):
            if(isinstance(tree.second, Real) and tree.second.name == name):
                tree.second = None

                tree.first.width = bitsobject
                return tree
            return tree
        if(isinstance(tree,Decl)):
            for d in tree.list:
                if(isinstance(d,Real) and d.name[0] == name):
                    d = bitsobject

            return tree
        
        for t in tree.children():
            AMSFileLinker._replace_port_type_by_name(t, name, bitsobject)
        return tree

    def _obtain_port_bitwidths(tree):

        if(not isinstance(tree, Node)):
            return []
        if(len(tree.children()) == 0):
            return []
        if(isinstance(tree,Ioport)):
            return [tree]
        arr = []
        for t in tree.children():
            arr = arr + AMSFileLinker._obtain_port_bitwidths(t)
        return arr


    def _get_instance_list(tree):
        if(not isinstance(tree, Node)):
            return []
        if isinstance(tree, Instance):
            return [tree]
        if(len(tree.children()) == 0):
            return []
        arr = []
        for t in tree.children():
            arr = arr + AMSFileLinker._get_instance_list(t)
        return arr
    
    def _get_unfilled_real_instances(tree):

        if(not isinstance(tree, Node)):
            return []
        if(len(tree.children()) == 0):
            return []
        if(isinstance(tree,Ioport)):
            if(isinstance(tree.second,Real)):
                return [tree]
            else:
                return []
        if(isinstance(tree,Decl)):
            if(isinstance(tree.children()[0],Real)):
                return [tree]
            else: 
                return []
        arr = []
        for t in tree.children():
            arr = arr + AMSFileLinker._get_unfilled_real_instances(t)
        return arr
    
    def _get_assign_dict(tree):
        if(not isinstance(tree, Node)):
            return {}
        if(len(tree.children()) == 0):
            return {}
        if(isinstance(tree,Assign)):
            return {tree.left.var.name: tree.right.var.name}
        arr = {}
        for t in tree.children():
            arr = {**arr, **AMSFileLinker._get_assign_dict(t)}
        return arr
    
    def _get_backwards_assign_dict(tree):
        if(not isinstance(tree, Node)):
            return {}
        if(len(tree.children()) == 0):
            return {}
        if(isinstance(tree,Assign)):
            return {tree.right.var.name: tree.left.var.name}
        arr = {}
        for t in tree.children():
            arr = {**arr, **AMSFileLinker._get_backwards_assign_dict(t)}
        return arr
    


        




        


        
        
