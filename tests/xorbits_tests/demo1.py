# import xorbits
# xorbits.init(init_local=True)
import xorbits.pandas as pd
import numpy as np
# import pandas as pd
import time
li = np.random.rand(100000000, 4)
df = pd.DataFrame(li, columns=list('abcd'))
st = time.time()
print(df.sum())
et = time.time()
print(et - st)
# pandas 7.545112133026123