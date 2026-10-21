import json,collections,sys
d=json.load(open(sys.argv[1]))
c=collections.Counter(); loc=collections.defaultdict(list); per=collections.Counter()
for n in d['nets']:
    for x in n.get('crossing_detail',[]):
        k=(x['kind'],'trace:'+x['ref_layer'],'plane:'+x['layer'])
        c[k]+=1; loc[k].append((round(x['x']),round(x['y']))); per[n['net_name'].replace('/CM5/','')]+=1
for k,v in c.most_common():
    print(k,v, collections.Counter(loc[k]).most_common(8))
print(per.most_common(40))
