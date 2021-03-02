"""Box example."""

from pandag import Pandag
from pandag.nodes import Assert, Output
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.DataFrame({'x': np.repeat(range(100), 100), 'y': list(range(100))*100})


algo = {
    # Assert's first argument is a pandas.query, which either matches or not
    Assert('x >= 60'): {
        False: {
               Assert('x < 40'): {
                    False: {
                        Assert('y >= 60'): {
                            False: {
                                Assert('y < 40'): {
                                    # You can use python 3.8's walrus operator to save
                                    # a node and re-use later.
                                    # Note that if you want to set a column to a new value (here color to black/red),
                                    # you have to provide a df.eval-compatible string. So if you want a string,
                                    # you have to quote it.
                                    # Plain `black` would mean here the black column.
                                    False: [BLACK := Output(_label='BLACK', color='"black"')],
                                    True: [RED := Output(_label='RED', color='"red"')],
                                },
                            },
                            True: RED,
                        },
                    },
                    True: RED,
                },
            },
        True: RED,
    }
}

p = Pandag(algo)
p.draw(fpath='box-dag.png', show_ids=True)
res_df = p.eval(df)
res_df.plot.scatter(x='x', y='y', c=df.color)
plt.savefig('box-output.png')
