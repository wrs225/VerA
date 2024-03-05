

from vera.linker.amslinker import AMSFileLinker
from test_mux import rtl_block

parseable = AMSFileLinker("./parseableverilogfile.v", preprocess_include_ams=[rtl_block])


parseable.link()