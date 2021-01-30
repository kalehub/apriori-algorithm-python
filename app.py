from flask import Flask, render_template, redirect, url_for, request, flash,session, send_from_directory
import os
from werkzeug.utils import secure_filename
import csv
from itertools import combinations



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/Users/teguhsatya/dev/myflask/uploads'
app.config['ALLOWED_EXTENSIONS'] = ['CSV']
app.secret_key = 'kale'


@app.route('/')
def index():
    return render_template('index.html')

def allowed_file(filename):
    if not "." in filename:
        return False
    ext = filename.split(".", 1)[1]

    if ext.upper() in app.config['ALLOWED_EXTENSIONS']:
        return True
    else:
        return False

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/upload', methods = ['POST', 'GET'])
def uploadDataset():
    if request.method == 'POST':
        if request.files:
            fi = request.files['thefile']
            minsup = request.form['minSup']
            mincon = request.form['minCon']
            if fi.filename == "":
                flash('No filename')
                return redirect(request.url)
            if allowed_file(fi.filename):
                filename = secure_filename(fi.filename)
                fi.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('result',filename=filename, ms = minsup, mc = mincon))
            else:
                flash('file extension is not allowed!')
                return redirect(request.url)


    return render_template('upload-dataset.html')

# ========== apriori logic =========
def readFile(fi):
    # with open(fi, 'r') as f:
    #     rd = csv.reader(f)
    # return list(rd)
    f = open(fi, 'r')
    rd = csv.reader(f)
    return list(rd)
    f.close()

def cleanData(fi):
    cl = list()
    for f in fi:
        f = [x for x in f if x != '']
        cl.append(f)
    return cl

def findFiter(cl, ms):
    # finding all the itemsets of size 1 and their support.
    fr = dict()
    greaterThanMin = list()
    for c in cl:
        for d in c:
            if d in fr:
                fr[d] += 1
            else:
                fr[d] = 1
    # keep only the itemsets with support 0.6
    for f in fr:
        # support -> occurence / number of trans
        if float(fr[f]/len(cl)) >= float(ms):
            greaterThanMin.append(f)
    return greaterThanMin

def generateUnique(fq):
    uniqueList = list()
    for f in fq:
        for q in f:
            if q not in uniqueList:
                uniqueList.append(q)
    return uniqueList

def makeCombination(ft, si):
    cb = list(combinations(ft,si))
    for c in range(0, len(cb)):
        temp = list(cb[c])
        cb[c] = temp
    return cb

def findSup(cl, ft, ms, si):
    print('calculating...')
    # making combination
    cb = makeCombination(ft,si)
    # print('size {} : {}'.format(si, cb))
    if len(cb)!=0:
        temp = list()
        for c in range(0, len(cb)):
            fr = 0
            for d in cl:
                count = 0
                for e in range(0, len(cb[c])):
                    if cb[c][e] in d:
                        count+=1
                    else:
                        count = 0
                    if count == len(cb[c]):
                        fr+=1
            if fr/len(cl) >= ms:
                temp.append(cb[c])
        uniqueEl = generateUnique(temp)
        ft = uniqueEl
        return findSup(cl,ft, ms,si+1)
    else:
        return ft

def findConVal(sa, ta, cl):
    # count the occurence of (sa and ta) as one list in cl ->upr 'upper'
    upr = 0
    blw = 0
    # combining the list
    temp = sa + ta
    for c in cl:
        flag = 0
        blwFlag = 0
        for t in temp:
            if t in c:
                flag+=1
            else:
                flag=0
        if flag==len(temp):
            upr+=1
        # count the occurence of ta in cl -> blw 'below'
        for u in ta:
            if u in c:
                blwFlag+=1
            else:
                blwFlag=0
        if blwFlag == len(ta):
            blw+=1
    # conf = upr/blw
    conf = float(upr/blw)
    return conf

def findAssocRule(sl,cl,mc,rl,cv):
    # cleaning
    for s in sl:
        if len(s) == 0 or len(s) == len(sl):
            sl.remove(s)
    print('{}'.format(sl))

    # membentuk calon aturan asosiasi
    print('Configuring association rules : ')
    # elemen yang akan diuji
    for s in sl:
        lengthOfS = len(s)
        for t in sl:
            if len(t) != lengthOfS:
                # check apakah ada nilai s di dalam t
                if len(s) == 1:
                    for u in s:
                        if u not in t:
                            # checking
                            # print(s, t)
                            conf = findConVal(s, t, cl)
                            if conf >= mc:
                                print('{}{} has {} confidence value'.format(s,t,conf))
                                rl.append(list(s))
                                rl.append(list(t))
                                cv.append(conf)
                else:
                    # for v in t :
                    #   if v not in s:
                    #     print(s,t)
                    count = 0
                    for a in s:
                        for b in t:
                            if a == b:
                                count += 1
                            else:
                                count += 0
                    if count == 0:
                        # checking
                        # print(s, t)
                        conf = findConVal(s, t, cl)
                        if conf >= mc:
                            print('{}{} has {} confidence value'.format(s,t,conf))
                            rl.append(list(s))
                            rl.append(list(t))
                            cv.append(conf)

    # print(rl)
    return rl,cv

def findConfidence(ni,cl, mc):
    # list of rules
    rl = list()
    # list of confidence value
    confVal = list()
    # make sublist (himpunan bagian)
    sl = makeSublist(ni)
    for s in sl:
        if len(s) == 0 or len(s) == len(ni):
            sl.remove(s)
    print('Sublist : ', sl)
    assocRule = findAssocRule(sl,cl,mc,rl,confVal)

    # changing confidence value to %
    for a in range(len(confVal)):
        confVal[a] = round(confVal[a]*100,2)



    return rl,confVal

def makeSublist(ni):
    base = []
    lists = [base]
    for i in range(len(ni)):
        orig = lists[:]
        new = ni[i]
        for j in range(len(lists)):
            lists[j] = lists[j] + [new]
        lists = orig + lists
    return lists

@app.route('/result/<filename>/minsupport/<ms>/minconfidence/<mc>')
def result(filename, ms, mc):
    # step 1 : read the file
    fi = readFile('uploads/'+filename)
    print('Uploaded file : {}'.format(fi))
    minSup = float(ms)/100
    minCon = float(mc)/100

    # step 2 : clean data (if there is blank)
    clData = cleanData(fi)
    print('Cleaned data : ', clData)

    # step 3 : finding all the itemset of size 1 and their support
    firstIter = findFiter(clData, minSup)
    if len(firstIter) == 0:
        flash('The minimum support is too big for the current dataset')
        return redirect(url_for('uploadDataset'))
    print('Size 1 : ',firstIter)

    # step 4 : generate itemsets of size 2 and compute their support.
    nextIter = findSup(clData,firstIter, minSup, si=2)
    print('Final iter : ',nextIter)

    # step 6 : find confidence and rules
    rules, confiValue = findConfidence(nextIter,clData, minCon)
    print('displaying rules and confidence value : {} {}'.format(rules, confiValue))



    # step 7 making a dictionary of rules and its values
    if len(confiValue) == 0:
        flash('The minimum confidence value is too big for the current dataset')
        return redirect(url_for('uploadDataset'))
    else:
        # turning association rules to a text (revision 1)
        assoc_rules = list()
        for i in range(0, len(rules),2):
            atr_asosiasi = 'If the patient '
            for r in rules[i]:
                atr_asosiasi += str(r)+' '
            atr_asosiasi += 'then '
            for r in rules[i+1]:
                atr_asosiasi+= str(r)+ ' '
            assoc_rules.append(atr_asosiasi)
        
        # displaying the result
        for k in range(0, len(assoc_rules)):
            print('{}. {} {}%'.format(k+1, assoc_rules[k], confiValue[k]*100))
        
        return render_template('result.html', theFile = filename, ms=ms, mc=mc, asc_role = assoc_rules, cf_value = confiValue, lenA = len(assoc_rules))

@app.route('/redo')
def redo():
    session.clear()
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(debug=True)