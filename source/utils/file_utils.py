import yaml


def yaml2dict(yaml_fn, Loader=yaml.SafeLoader):
    ''' Read from yaml_fn and return a dict '''
    with open(yaml_fn) as fh:
        yaml_dict = yaml.load(fh)
    return yaml_dict
