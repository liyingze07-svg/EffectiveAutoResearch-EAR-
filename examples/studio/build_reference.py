"""Build parameterized authored reference walkthroughs. No EAR model run or novelty claim.

ReportLab is only needed when regenerating the bundled PDFs; serving the demo
uses Python's standard library and the committed reference.json.
"""
from pathlib import Path
from html import escape
import base64
import csv
import io
import json
import math
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Flowable

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
SOURCE='https://web.stanford.edu/~boyd/cvxbook/'

def trajectory(mode, epsilon=.1):
    x=[1.0,1.0];rows=[]
    for k in range(81):
        bound=0.9**k*math.sqrt(2)+sum(.1*epsilon*0.9**(k-1-s)/(s+1 if mode=='decay' else 1) for s in range(k))
        rows.append({'step':k,'x1':x[0],'x2':x[1],'norm':math.hypot(*x),'bound':bound})
        eps=epsilon/(k+1) if mode=='decay' else epsilon
        x=[.9*x[0]-.1*eps,0.0]
    return rows

class Plot(Flowable):
    width=460;height=200
    def __init__(self,mode,epsilon):
        super().__init__()
        self.mode,self.epsilon=mode,epsilon
        self.width,self.height=460,200
    def draw(self):
        c=self.canv;rows=trajectory(self.mode,self.epsilon);left,bottom,w,h=39,32,403,144
        c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#766a85'))
        for val in [0,.5,1,1.5]:
            y=bottom+val/1.6*h;c.setStrokeColor(colors.HexColor('#e9e3ed'));c.line(left,y,left+w,y);c.drawRightString(left-7,y-3,str(val))
        for field,col in [('bound','#8056a9'),('norm','#37313f')]:
            p=c.beginPath();p.moveTo(left,bottom+rows[0][field]/1.6*h)
            for row in rows[1:]:p.lineTo(left+row['step']/80*w,bottom+row[field]/1.6*h)
            c.setStrokeColor(colors.HexColor(col));c.setLineWidth(1.9);c.drawPath(p)
        for k in [0,20,40,60,80]:c.drawCentredString(left+k/80*w,bottom-14,str(k))
        c.drawCentredString(left+w/2,1,'Iteration')
        c.setFillColor(colors.HexColor('#37313f'));c.drawString(40,184,'Observed distance to optimum')
        c.setFillColor(colors.HexColor('#8056a9'));c.drawString(255,184,'Proved upper bound')

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='PaperTitle',fontName='Times-Bold',fontSize=23,leading=28,alignment=TA_CENTER,spaceAfter=12))
styles.add(ParagraphStyle(name='PaperMeta',fontName='Helvetica',fontSize=8,leading=12,alignment=TA_CENTER,textColor=colors.HexColor('#75697f'),spaceAfter=18))
styles.add(ParagraphStyle(name='PaperBody',fontName='Times-Roman',fontSize=11,leading=16,spaceAfter=11))
styles.add(ParagraphStyle(name='PaperHead',fontName='Times-Bold',fontSize=13,leading=18,spaceBefore=9,spaceAfter=7))
styles.add(ParagraphStyle(name='Equation',fontName='Courier',fontSize=10,leading=16,alignment=TA_CENTER,spaceBefore=7,spaceAfter=13))

def footer(c,doc):
    c.saveState();c.setStrokeColor(colors.HexColor('#d8d0df'));c.line(62,51,533,51)
    c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#82768c'));c.drawString(62,36,'EAR | Authored reference workflow | No model calls');c.drawRightString(533,36,str(doc.page));c.restoreState()

def build_reference(mode,epsilon):
    constant=mode=='constant'
    title='Inexact Gradient Descent: A Residual Bound' if constant else 'Inexact Gradient Descent: Recovering Convergence'
    goal='Bound the residual under persistent gradient error.' if constant else 'Recover exact convergence when gradient error decays.'
    result='For step sizes up to 1/L, bounded gradient error gives an asymptotic residual bound of epsilon / mu. Constant bias can attain this bound.' if constant else 'If the error bound tends to zero, the stable convolution tends to zero. Exact convergence follows, although a linear rate need not.'
    theorem='For Q symmetric positive definite with spectrum in [mu, L], 0 < eta < 2 / L and q = max(|1-eta*mu|, |1-eta*L|) < 1, the iterates x[k+1] = (I-eta*Q)x[k] - eta*e[k], with ||e[k]|| <= epsilon[k], satisfy'
    equation='||x[k]|| <= q^k ||x[0]|| + eta sum(s=0..k-1) q^(k-1-s) epsilon[s].'
    corollary='If epsilon[s] <= epsilon, limsup ||x[k]|| <= eta*epsilon/(1-q). For eta <= 1/L, q=1-eta*mu and the bound becomes epsilon/mu.' if constant else 'If epsilon[s] tends to zero, ||x[k]|| tends to zero. This claim concerns positive-definite quadratics and does not assert a linear rate for arbitrary decaying errors.'
    proof='Diagonalize Q in an orthonormal eigenbasis. The spectral norm of I-eta*Q is at most q. Applying the triangle inequality gives ||x[k+1]|| <= q||x[k]|| + eta*epsilon[k]. Induction unrolls this recurrence into the stated bound.'
    tail='For a uniformly bounded error, the geometric series is at most 1/(1-q). If eta <= 1/L, the endpoint factors are nonnegative and q=1-eta*mu.' if constant else 'For any delta > 0, choose N such that epsilon[s] <= delta for s >= N. The finite prefix of the convolution vanishes as k grows; the remaining tail is at most eta*delta/(1-q). Taking a limit superior and then delta to zero proves the claim.'
    counter='In one dimension, take Q=mu, x[0]=0 and e[k]=epsilon. Then x[k] = -(epsilon/mu)(1-(1-eta*mu)^k), so x[k] tends to -epsilon/mu instead of zero.'
    candidate='Bounded gradient errors do not prevent exact convergence.' if constant else 'Any decaying gradient error preserves a linear convergence rate.'
    if not constant:
        counter='In one dimension, take Q=mu, x[0]=0, 0<eta<=1/mu and e[k]=epsilon/(k+1). The contributions to x[k] have one sign, so |x[k]| >= eta*epsilon/k. This lower bound excludes a geometric rate.'
    review='R1: Make the spectral assumptions and step-size range explicit in the theorem. R2: Complete the '+('geometric-series bound and its constant-bias boundary case.' if constant else 'finite-prefix / vanishing-tail argument; convergence alone is not a rate guarantee.')
    revision='Added the spectral assumptions and complete supporting argument. The established research conclusion is retained; numerical evidence remains separate from the proof.'
    schedule=f'{epsilon:.2f}'+('/(k+1)' if not constant else '')
    rows=trajectory(mode,epsilon)
    csvbuf=io.StringIO();w=csv.DictWriter(csvbuf,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    plan=f'# Research plan\n\nObjective: {goal}\n\nScope: f(x)=1/2 x^T Q x; Q symmetric positive definite.\n1. Inspect the standard exact-gradient recurrence.\n2. Derive a perturbation bound without hiding the error term.\n3. Challenge the candidate claim against the selected error schedule.\n4. Verify a two-dimensional quadratic numerically.\n5. Write a manuscript; revise against the prepared review.\n\nReference: Boyd and Vandenberghe, Convex Optimization, chapter 9.\n{SOURCE}\n\nProvenance: Authored reference scenario mapped to AutonomousMath skills. Not a recorded EAR model episode or a new result.\n'
    plan=plan.replace('\n\nScope:',f'\n\nCandidate: {candidate}\nSkeptic: {counter}\nEstablished result: {result}\n\nScope:')
    proofmd=f'# Proof and scope\n\n{theorem}\n\n{equation}\n\n{proof}\n\n{tail}\n\n## Corollary\n{corollary}\n\n## Skeptic counterexample\n{counter}\n\nThis is a standard illustrative task, not a claim of novelty or formal verification.\n'
    v1claim=result
    v1=f'# {title} - Draft v1\n\nAUTHORED, INTENTIONALLY INCOMPLETE DRAFT\n\n## Abstract\n{result}\n\n## Derivation\n{proof}\n\n## Established result\n{v1claim}\n\n## Numerical check\nError schedule: {schedule}. Final norm: {rows[-1]["norm"]:.8f}.\n\nThe research conclusion is retained. The draft omits explicit spectral assumptions and the complete supporting boundary argument. It is not an EAR-generated manuscript.\n'
    v2=f'# {title} - Revised v2\n\nAuthored reference manuscript. No model calls; no novelty or conference acceptance claim.\n\n## Abstract\n{result}\n\n## Setting and theorem\n{theorem}\n\n{equation}\n\n{corollary}\n\n## Proof\n{proof}\n\n{tail}\n\n## Boundary case\n{counter}\n\n## Numerical check\nQ=diag(1,10), eta=0.1, x[0]=(1,1), e[k]=('+schedule+',0). 81 saved states; the proved bound holds at all of them. Final norm at k=80: '+f'{rows[-1]["norm"]:.8f}'+'. Numerical agreement is not a proof.\n\n## Review and revision\n'+review+'\n\n'+revision+'\n\n## Limitations\nKnown quadratic result; no claim for general nonlinear objectives. Model reviews in the full EAR engine are not formal proof or conference acceptance. The review above is prepared demonstration feedback.\n\n## Reference\nBoyd and Vandenberghe, Convex Optimization, chapter 9.\n'+SOURCE+'\n'
    tex=r'\documentclass[11pt]{article}'+'\n'+r'\usepackage[margin=1in]{geometry}'+'\n'+r'\usepackage{amsmath,amssymb}'+'\n'+r'\title{'+title+r'}\author{EAR Authored Reference Walkthrough}\date{}\begin{document}\maketitle'+'\n'+r'\begin{abstract}'+result+r'\end{abstract}'+'\n'+r'\section{Setting and theorem}Let $Q$ be symmetric positive definite, with $\mu I\preceq Q\preceq LI$. Choose $0<\eta<2/L$ and $q=\max\{|1-\eta\mu|,|1-\eta L|\}<1$. For $x_{k+1}=(I-\eta Q)x_k-\eta e_k$ and $\|e_k\|\le\epsilon_k$,'+'\n'+r'\[\|x_k\|\le q^k\|x_0\|+\eta\sum_{s=0}^{k-1}q^{k-1-s}\epsilon_s.\]'+'\n'+r'\section{Proof}'+proof+' '+tail+'\n'+r'\section{Corollary}'+corollary+'\n'+r'\section{Boundary case}'+counter+'\n'+r'\section{Numerical check}We use $Q=\mathrm{diag}(1,10)$, $\eta=0.1$, $x_0=(1,1)$ and '+('$e_k=('+schedule+',0)$.')+' 81 saved states obey the bound. This numerical check is not a proof.\n'+r'\section{Provenance and limitations}An authored reference task, not an EAR model episode or a new research result. Prepared review feedback led to explicit scope and the complete boundary argument. No conference acceptance or formal verification is claimed.'+'\n'+r'\begin{thebibliography}{1}\bibitem{boyd}S. Boyd and L. Vandenberghe. Convex Optimization. Cambridge University Press, 2004. Chapter 9.\end{thebibliography}\end{document}'+'\n'
    path=OUT/(f'EAR-reference-{mode}.pdf' if epsilon==.1 else f'EAR-reference-{mode}-e{epsilon:.2f}.pdf')
    story=[]
    def p(text,style='PaperBody'):story.append(Paragraph(escape(text),styles[style]))
    p(title,'PaperTitle');p('EAR reference walkthrough | Revised manuscript v2 | Prepared demonstration','PaperMeta')
    p('Abstract','PaperHead');p(result)
    p('1  Setting and theorem','PaperHead');p(theorem);p(equation,'Equation');p(corollary)
    p('2  Proof','PaperHead');p(proof);p(tail)
    story.append(PageBreak())
    p('3  Boundary case','PaperHead');p(counter)
    p('4  Numerical validation','PaperHead');p('We use Q = diag(1,10), eta = 0.1 and x[0] = (1,1). The gradient error is '+('e[k] = ('+schedule+',0).')+' All 81 saved states satisfy the theorem bound. This check illustrates the argument and is not a proof.')
    story.append(Plot(mode,epsilon));p(f'Figure 1. Distance to the optimum and the proved upper bound. At iteration 80, the observed norm is {rows[-1]["norm"]:.6f}.','PaperMeta')
    p('5  Review and revision','PaperHead');p(review);p(revision)
    p('6  Limitations and provenance','PaperHead');p('This standard quadratic result and its review were authored for an interactive EAR reference workflow. They are not outputs of an EAR model episode, a new contribution, a formal proof certificate, or conference acceptance. Scope does not extend to general nonlinear objectives.')
    p('Reference','PaperHead');p('S. Boyd and L. Vandenberghe. Convex Optimization. Cambridge University Press, 2004. Chapter 9. '+SOURCE)
    SimpleDocTemplate(str(path),pagesize=(595,842),rightMargin=62,leftMargin=62,topMargin=58,bottomMargin=65,title=title,author='EAR reference walkthrough').build(story,onFirstPage=footer,onLaterPages=footer)
    return {'error_level':epsilon,'candidate_claim':candidate,'title':title,'goal':goal,'result':result,'theorem':theorem,'equation':equation,'corollary':corollary,'proof':proof,'tail':tail,'counterexample':counter,'review':review,'revision':revision,'draft_claim':v1claim,'plan':plan,'proof_md':proofmd,'v1':v1,'v2':v2,'tex':tex,'csv':csvbuf.getvalue(),'rows':rows,'pdf':base64.b64encode(path.read_bytes()).decode(),'provenance':'authored_reference_workflow','model_calls':0}
data={}
for mode in ['constant','decay']:
    variants={f'{epsilon:.2f}':build_reference(mode,epsilon) for epsilon in [.05,.1,.2]}
    data[mode]={**variants['0.10'],'variants':variants}
(ROOT/'examples/studio/reference.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Built six parameter-matched reference manuscript PDFs and portable artifact data.')
