from collections import defaultdict
import logging
import networkx as nx

from smanalyzer.models.ApplicationInfo import ApplicationInfo
from smanalyzer.models.ActivityInfo import ActivityInfo
from androguard.misc import AnalyzeAPK
from androguard.core.analysis.analysis import Analysis
from androguard.core.analysis.analysis import ClassAnalysis
from androguard.core.dex import EncodedMethod
from androguard.core.analysis.analysis import MethodAnalysis

class CodeAnalyzer:

    # Landroid/app/Activity;
    SET_MIXED_CONTENT_MODE = [
        "setMixedContentMode (I)V",
    ]

    application_info: ApplicationInfo
    call_graph: nx.DiGraph
    dx: Analysis

    def __init__(self, application_info: ApplicationInfo, dx: Analysis):
        self.application_info = application_info
        self.dx = dx
        self.override_methods: list[MethodAnalysis] = []

    def analyze(self):
        logging.info(f"Analyzing code for {self.application_info.package_name}")

        set_mixed_content_mode_methods: list[MethodAnalysis] = []

        for c in self.dx.get_classes():
            for method_analysis in c.get_methods():
                encoded_method: EncodedMethod = method_analysis.get_method()
                full_name: str = method_analysis.name
                if full_name == "setMixedContentMode":
                    class_name = encoded_method.get_class_name()
                    if (self.is_class_subclass_of(class_name, "Landroid/webkit/WebSettings;")):
                        set_mixed_content_mode_methods.append(method_analysis)

        call_locations = []

        for m in set_mixed_content_mode_methods:
            m: MethodAnalysis
            xrefs: list[tuple[ClassAnalysis, MethodAnalysis, int]] = m.get_xref_from()
            for xref in xrefs:
                caller_method = xref[1]

                method_instructions = []
                register_values = defaultdict(list)

                for instruction in caller_method.get_method().get_instructions():
                    print(f"-- {instruction}")
                    operands = instruction.get_operands()
                    op_value = instruction.get_output()

                    method_instructions.append(operands)

                    # track constant assignments
                    if instruction.get_name().startswith("const/4"):
                        reg = operands[0][1] # register name, e.g., v1
                        value = operands[1][1] # constant value
                        register_values[reg].append(value)
                        #print(f"Register: {reg}, Value: {value}")

                    # detect invoke-virtual call to setMixedContentMode
                    if "setMixedContentMode" in op_value:
                        #print(operands)
                        instance_register = operands[0][1]  # First register = WebSettings instance
                        param_register = operands[1][1]  # Last register = actual parameter
                        param_values = []

                        # get the actual parameter value
                        if param_register in register_values:
                            param_values = register_values[param_register]

                        call_locations.append((caller_method, param_values))

        
        for caller_method, param_values in call_locations:
            if caller_method.full_name not in self.application_info.mixed_content_calls:
                self.application_info.mixed_content_calls[caller_method.full_name] = param_values
            else:
                self.application_info.mixed_content_calls[caller_method.full_name] = list(set(self.application_info.mixed_content_calls[caller_method.full_name] + param_values))

        return