import requests
import pathlib
import argparse
import collections

# local imports
import secrets
import config


def post(docid, conf):
    if not (isinstance(docid, int) or 1 <= docid):
        raise ValueError("docid must be an  positive integer!")

    r = requests.get(f'http://0.0.0.0:{conf.PORT}/db/{conf.SECRET_DB_URL}/{docid}')
    print(r.content.decode('utf'))


#  def rebuild(conf):
#      "run to rebuild the entire database"
#      return deploy(conf)
    

def get_docid_range(conf):
    "run to build the entire database"
    post_counts = {'.md': collections.Counter(), '.meta': collections.Counter()}
    for ext, dir_ in (('.md', conf.POSTS_MARKDOWN_DIR), ('.meta', conf.POSTS_META_DIR)):
        for path in dir_.iterdir():
            count = path.name.split('_', 1)[0]
            if count.isnumeric() and path.suffix == ext:
                post_counts[ext][int(count)] += 1

    # TODO better error reporting!
    for d in post_counts.values():
        assert len(d) == sum(d.values()) == max(d.keys())
        assert min(d.keys()) == 1
    return list(range(1, max(post_counts['.md'].keys()) + 1))


def deploy(conf):
    for docid in get_docid_range(conf):
        post(docid, conf)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--post', help='Post docid', type=int, default=None)
    parser.add_argument('--deploy', default=False, action='store_true')
    parser.add_argument('--devel', default=False, action='store_true')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    conf = config.get_conf(args.devel)
    if args.post is not None:
        post(args.post, conf)
    if args.deploy:
        deploy(conf)


if __name__ == '__main__':
    main()
