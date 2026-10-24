#!/usr/bin/env python3
"""gpm: post POST.final.md as a new top-level comment on discussion #118, then POST_2.final.md and POST_3.final.md
as replies to it; or, with --edit, replace the three bodies with the current POST*.final.md (after filing).

    python3 -X utf8 wk/gpm/_staging/post_comments.py          # posts what is not posted yet (posted.json)
    python3 -X utf8 wk/gpm/_staging/post_comments.py --edit   # updates all three in place

Resumable: posted.json records each comment's node id and URL as soon as it exists.
"""
import json
import os
import subprocess
import sys

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REC = os.path.join(G, 'posted.json')
done = json.load(open(REC)) if os.path.exists(REC) else {}


def gql(query, **vars):
    args = ['gh', 'api', 'graphql', '-f', f'query={query}']
    for k, v in vars.items():
        args += ['-F', f'{k}=@{v}'] if k == 'body' else ['-f', f'{k}={v}']
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'gh api failed: {r.stderr.strip()[:500]}')
    return json.loads(r.stdout)['data']


ADD = 'mutation($id:ID!,$body:String!){addDiscussionComment(input:{discussionId:$id,body:$body}){comment{id url}}}'
REPLY = ('mutation($id:ID!,$reply:ID!,$body:String!){addDiscussionComment(input:{discussionId:$id,replyToId:$reply,'
         'body:$body}){comment{id url}}}')
EDIT = 'mutation($cid:ID!,$body:String!){updateDiscussionComment(input:{commentId:$cid,body:$body}){comment{id url}}}'

if '--edit' in sys.argv:
    for name in ('POST', 'POST_2', 'POST_3'):
        c = gql(EDIT, cid=done[name]['id'], body=os.path.join(G, f'{name}.final.md'))['updateDiscussionComment']['comment']
        print('edited', name, c['url'])
    sys.exit(0)

if 'discussion' not in done:
    q = 'query{repository(owner:"drandyhaas",name:"KiCadRoutingTools"){discussion(number:118){id title}}}'
    d = gql(q)['repository']['discussion']
    done['discussion'] = d['id']
    print('discussion #118:', d['title'])
for name in ('POST', 'POST_2', 'POST_3'):
    if name in done:
        print('already posted', name, done[name]['url'])
        continue
    body = os.path.join(G, f'{name}.final.md')
    if name == 'POST':
        c = gql(ADD, id=done['discussion'], body=body)['addDiscussionComment']['comment']
    else:
        c = gql(REPLY, id=done['discussion'], reply=done['POST']['id'], body=body)['addDiscussionComment']['comment']
    done[name] = c
    json.dump(done, open(REC, 'w'), indent=1)
    print('posted', name, c['url'])
