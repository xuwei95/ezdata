import time
import xorbits
# xorbits.init("http://10.0.4.16:8008")
# xorbits.init(init_local=True)
import xorbits.numpy as np
# import numpy as np
st = time.time()
print(np.random.rand(100000, 100000).mean())
et = time.time()
print(et - st)
