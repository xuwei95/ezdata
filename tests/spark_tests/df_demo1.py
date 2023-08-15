from datetime import datetime, date
from pyspark.sql import Row

import pyspark.pandas as pd
li = [{
    'a': 1,
    'b': 'hahah'
}]
df = pd.DataFrame(li)
print(df)