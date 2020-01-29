# A place to put utility functions for dealing with collections
# (lists, sets, dictionaries, etc)
#  ~ Matthew Seiler

def index_selector(key):
    """
    Returns a function that, given a value, deindexes that value with the given key.
    Examples::

        # Extract the same value from each dictionary in a list of dictionaries
        select_my_key = index_selector('my_key')
        [select_my_key(d) for d in list_of_dictionaries]

        # extract the first item from each list in a list of lists
        select_first = index_selector(0)
        [select_first(l) for l in list_of_lists]

    :param key: any value
    :type key: K
    :return: a function that deindexes a new value with the given key
    :rtype: function Container<T> -> T
    """

    return lambda x: x[key]

def group_by_selector(items, selector):
    """
    Groups the items in a list into a dictionary of lists, using the given selector function to create keys.

    Each key in the resulting dictionary will map to a list of items from the original list that
    matched that key. The key for each item is produced by passing that item to the selector function.

    Example::

        even_or_odd = lambda n: 'even' if n % 2 == 0 else 'odd'
        numbers = range(10)
        grouped = group_by_selector(numbers, even_or_odd)
        # { 'even': [0, 2, 4, 6, 8], 'odd': [1, 3, 5, 7, 9] }

    :param items: collection to group
    :type items: iterable<T>
    :param selector: creates a grouping key from an item
    :type selector: function T -> K
    :return: a dictionary that groups the list elements by the selected key
    :rtype: dict<K,List<T>>
    """
    result = dict()
    for item in items:
        key = selector(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result

def group_by(selector):
    """
    Parameterized version of group_by_selector that lets you construct a grouping function
    for a particular selector function and re-use it multiple times. So instead of::

        first_groups = group_by_selector(list1, some_selector)
        second_groups = group_by_selector(list2, some_selector)

    You can say::

        group_by_some_selector = group_by(some_selector)
        first_groups = group_by_some_selector(list1)
        second_groups = group_by_some_selector(list2)

    :param selector: function to produce a grouping key for each item in an iterable
    :type selector: T -> K
    :return: a function that groups iterables into disjoint lists using 'selector'
    :rtype: function Iterable<T> -> dict<K, List<T>>
    """
    return lambda items: group_by_selector(items, selector)