import yaml
import os

# #####     PROCESS NEW FILE      ######

def write_info(doc):
    pass


def save_file(doc):
    pass


def check_file(doc):
    pass


def process_new_file(doc):
    check_file(doc)
    save_file(doc)
    write_info(doc)



# #####     FUNCTIONS FOR RUN TEST      ######

def load_test(filename):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    path_file = os.path.join(os.path.split(cur_dir)[0], 'data', 'tests', filename)
    if not os.path.exists(path_file):
        print(f'file do not exist {path_file}')
        return

    with open(path_file, 'r') as f:    
        data = yaml.load(f, Loader=yaml.FullLoader)
        print(data)


load_test('test_zero.yaml')




