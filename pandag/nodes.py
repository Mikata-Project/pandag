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

    def __init__(self, query, _label=None, _id=None, _x=None, _y=None,
                 local_dict=None, global_dict=None):
        self.query = query
        self.label = _label
        self.id = _id
        self._x = _x
        self._y = _y
        self.local_dict = local_dict
        self.global_dict = global_dict
        if not _label:
            self.label = query

    def eval(self, df, edge_data):
        res = df.eval(self.query,
                      local_dict=self.local_dict,
                      global_dict=self.global_dict)
        if edge_data['label']:
            return res
        return np.invert(res)


class Output(Node):
    """Output node sets new values."""
    plot_shape = 'o'

    def __init__(self, _label=None, _id=None, _x=None, _y=None, expr=None,
                 local_dict=None, global_dict=None, **kw):
        self.label = _label
        self.id = _id
        self._x = _x
        self._y = _y
        self.expr = expr
        self.local_dict = local_dict
        self.global_dict = global_dict
        self.kw = kw

    def update(self, df, loc):
        for k, v in self.kw.items():
            if callable(v):
                df.loc[loc, k] = df.apply(v, axis=1)
            else:
                df.loc[loc, k] = df.eval(v,
                                         local_dict=self.local_dict,
                                         global_dict=self.global_dict)
        if self.expr:
            # If there was an eval expression specified, update matching rows
            # with it.
            # Expressions can update multiple columns, if separated by newlines
            eval_df = df.eval(self.expr,
                              local_dict=self.local_dict,
                              global_dict=self.global_dict)
            df.loc[loc, eval_df.columns] = eval_df


class Inequal(Node):
    """Inequal node evaluates a given condition."""
    plot_shape = 'h'

    def __init__(self, _label=None, _id=None, _x=None, _y=None,
                 local_dict=None, global_dict=None, **kw):
        self.label = _label
        self.id = _id
        self._x = _x
        self._y = _y
        self.local_dict = local_dict
        self.global_dict = global_dict
        self.kw = kw

    def eval(self, df, edge_data):
        return df.eval(edge_data['label'],
                       local_dict=self.local_dict,
                       global_dict=self.global_dict)


class Dummy(Node):
    """Dummy node is just a placeholder for presentation purposes."""
    plot_shape = 's'

    def __init__(self, _label=None, _id=None, _x=None, _y=None):
        self.label = _label
        self.id = _id
        self._x = _x
        self._y = _y
