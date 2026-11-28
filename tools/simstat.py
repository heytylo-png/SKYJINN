import json,sys,collections
R=[]
for f in sys.argv[1:]:R+=json.load(open(f))
F=['djinn','verdant','mutant','knight','goblin','undead','auto','dragon','frost','demon']
def summ(rs,label):
    n=len(rs)
    if not n:return
    t=sum(r['t'] for r in rs)/n/60;ko=sum(r['why']=='ko' for r in rs)/n
    short=sum(r['t']<210 for r in rs)/n;long_=sum(r['t']>330 for r in rs)/n
    print(f"{label:<16} n={n:4d} avg {t:4.2f} min  KO {ko*100:5.1f}%  timer {100-ko*100:5.1f}%  <3.5min {short*100:4.1f}%  >5.5min {long_*100:4.1f}%")
summ(R,'ALL')
for d in ['normal','hard']:summ([r for r in R if r['d']==d],d)
for m in ['dunes','bridge','volcano']:summ([r for r in R if r['m']==m],m)
print()
print(f"{'faction':<9} {'win%':>6} {'(N)':>5} {'(H)':>5} {'dunes':>6} {'bridge':>6} {'volc':>6} {'avg min':>8}")
for f in F:
    def wr(rs):
        g=[r for r in rs if f in (r['a'],r['b'])];
        if not g:return float('nan')
        s=0
        for r in g:
            me=0 if r['a']==f else 1
            s+=0.5 if r['win']<0 else (1 if r['win']==me else 0)
        return s/len(g)*100
    g=[r for r in R if f in (r['a'],r['b'])]
    print(f"{f:<9} {wr(R):6.1f} {wr([r for r in R if r['d']=='normal']):5.1f} {wr([r for r in R if r['d']=='hard']):5.1f} {wr([r for r in R if r['m']=='dunes']):6.1f} {wr([r for r in R if r['m']=='bridge']):6.1f} {wr([r for r in R if r['m']=='volcano']):6.1f} {sum(r['t'] for r in g)/len(g)/60:8.2f}")
side=sum(1 for r in R if r['win']==0)/len(R)*100;print(f"\nleft side wins {side:.1f}%  draws {sum(r['win']<0 for r in R)/len(R)*100:.1f}%")
