# Copyright 2014-2015 National Institute of Advanced Industrial Science and Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

def getLogger(prog = ""):
    # create logger
    logger = logging.getLogger(prog)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s[%(name)s][%(levelname)s]: %(message)s")
    # add formatter to ch
    handler.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(handler)
    return logger

if __name__ == "__main__":
    logger = getLogger("test")
    logger.error("start LOG from TNRM to NSI. ERROR")
    logger.info("start LOG from TNRM to NSI. INFO")
    logger.debug("start proxy from TNRM to NSI. DEBUG")
