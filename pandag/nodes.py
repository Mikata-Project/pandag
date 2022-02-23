"""Pandag nodes."""
import numpy as np


class Node:
    @classmethod
    def get_subclasses(cls):
        """Return all subclasses."""
        for subclass in cls.__subclasses__():
            yield from subclass.get_subclasses()
            yield subclass

    def eval(self, df, edge_data):
        """Return True for all rows."""
        return [True]*len(df)

    def update(self, df, loc):
        pass


class Assert(Node):
    """Assert node partitions the rows into two based on the incoming condition."""
    plot_shape = '>'

    def __init__(self, query, _label=None, _id=None):
        self.query = query
        self.label = _label
        self.id = _id
        if not _label:
            self.label = query

    def eval(self, df, edge_data):
        res = df.eval(self.query)
        if edge_data['label']:
            return res
        return np.invert(res)


class Output(Node):
    """Output node sets new values."""
    plot_shape = 'o'

    def __init__(self, _label=None, _id=None, expr=None, **kw):
        self.label = _label
        self.id = _id
        self.expr = expr
        self.kw = kw

    def update(self, df, loc):
        for k, v in self.kw.items():
            if callable(v):
                df.loc[loc, k] = df.apply(v, axis=1)
            else:
                df.loc[loc, k] = df.eval(v)
        if self.expr:
            # If there was an eval expression specified, update matching rows
            # with it.
            # Expressions can update multiple columns, if separated by newlines
            eval_df = df.eval(self.expr)
            df.loc[loc, eval_df.columns] = eval_df


class Inequal(Node):
    """Inequal node evaluates a given condition."""
    plot_shape = 'h'

    def __init__(self, _label=None, _id=None, **kw):
        self.label = _label
        self.id = _id
        self.kw = kw

    def eval(self, df, edge_data):
        return df.eval(edge_data['label'])


class Dummy(Node):
    """Dummy node is just a placeholder for presentation purposes."""
    plot_shape = 's'

    def __init__(self, _label=None, _id=None):
        self.label = _label
        self.id = _id
