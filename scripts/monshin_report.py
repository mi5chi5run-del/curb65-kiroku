# -*- coding: utf-8 -*-
# 外来問診記録版 週次レポートPDF（GitHub Actions用）
#  - データは同ディレクトリの data.json（Supabaseから取得済み）を読む
#  - 日本語フォントは Ubuntu の Noto Sans CJK JP を使う
#  - 出力は report.pdf
import os, json, statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages

# --- 日本語フォント（Noto CJK）を確実に読み込む ---
for fp in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
           '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
           '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf']:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
        plt.rcParams['font.family'] = fm.FontProperties(fname=fp).get_name()
        break
plt.rcParams['axes.unicode_minus'] = False

DATE = os.environ.get('REPORT_DATE', '')
data = json.load(open('data.json', encoding='utf-8'))
n = len(data)

# ---------- 集計 ----------
ages = [d['age'] for d in data if isinstance(d.get('age'), (int, float))]
mean = statistics.mean(ages) if ages else 0.0
sd = statistics.stdev(ages) if len(ages) > 1 else 0.0
amin, amax = (min(ages), max(ages)) if ages else (0, 0)
male   = sum(1 for d in data if d.get('sex') == '男')
female = sum(1 for d in data if d.get('sex') == '女')
smk = {'非喫煙': 0, '元喫煙': 0, '現喫煙': 0}
for d in data:
    if d.get('smoking_status') in smk:
        smk[d['smoking_status']] += 1

def rate_list(keys_labels):
    out = []
    for label, k in keys_labels:
        vals = [d for d in data if d.get(k) in ('あり', 'なし')]
        pos = sum(1 for d in vals if d[k] == 'あり')
        tot = len(vals)
        out.append((label, pos / tot * 100 if tot else 0.0, pos, tot))
    return out

def draw_barh(ax, rows, color, title):
    labels = [r[0] for r in rows][::-1]; vals = [r[1] for r in rows][::-1]
    poss = [r[2] for r in rows][::-1]; tots = [r[3] for r in rows][::-1]
    ax.barh(labels, vals, color=color)
    ax.set_xlim(0, 118); ax.set_xlabel('「あり」割合（%）', fontsize=9)
    ax.set_title(title, fontsize=13, weight='bold'); ax.tick_params(labelsize=9)
    for i, (v, p, t) in enumerate(zip(vals, poss, tots)):
        ax.text(min(v + 2, 104), i, f'{v:.0f}% ({p}/{t})', va='center', fontsize=7.5, color='#333333')

SYMPTOMS = [('気管支喘息', 'asthma'), ('花粉症', 'hay_fever'), ('職業曝露', 'dust_exposure_job'),
            ('鳥飼育', 'bird'), ('犬飼育', 'dog'), ('猫飼育', 'cat')]
EXPO = [('鳥', 'bird'), ('犬', 'dog'), ('猫', 'cat'), ('カビ', 'mold_exposure'),
        ('加湿器', 'humidifier'), ('羽毛布団', 'feather_bedding'), ('園芸', 'gardening'),
        ('24時間風呂', 'hot_spring_bath'), ('職業粉塵', 'dust_exposure_job'),
        ('アスベスト', 'asbestos'), ('シリカ', 'silica'), ('木材粉塵', 'wood_dust')]
HISTORY = [('気管支喘息', 'asthma'), ('花粉症', 'hay_fever'), ('アトピー', 'atopic_dermatitis'),
           ('薬剤アレルギー', 'drug_allergy'), ('関節リウマチ', 'rheumatoid_arthritis'),
           ('SLE', 'sle'), ('強皮症', 'systemic_sclerosis'), ('血管炎', 'vasculitis'),
           ('結核', 'tuberculosis'), ('NTM', 'ntm'), ('肺がん', 'lung_cancer'), ('副鼻腔炎', 'sinusitis')]
FAMILY = [('喘息', 'family_asthma'), ('結核/NTM', 'family_tb_ntm'), ('膠原病', 'family_autoimmune'),
          ('肺がん', 'family_lung_cancer'), ('その他がん', 'family_other_cancer'),
          ('糖尿病', 'family_diabetes'), ('高血圧', 'family_hypertension'),
          ('ILD/サルコイドーシス', 'family_ild_sarcoidosis')]

def pack_years(d):
    cigs = d.get('cigarettes_per_day'); start = d.get('smoking_start_age'); end = d.get('smoking_end_age')
    age = d.get('age')
    if not isinstance(cigs, (int, float)) or not isinstance(start, (int, float)):
        return None
    if not isinstance(end, (int, float)):
        end = age
    if not isinstance(end, (int, float)):
        return None
    yrs = end - start
    return cigs / 20 * yrs if yrs > 0 else None

smokers = []
for d in data:
    if d.get('smoking_status') in ('元喫煙', '現喫煙'):
        py = pack_years(d)
        if py is not None:
            sid = str(d.get('patient_id', '')).replace('ダミー ', '').split('（')[0]
            smokers.append((sid, py))

pp = PdfPages('report.pdf')

# ===== P1 =====
fig = plt.figure(figsize=(8.27, 11.69), dpi=150); fig.patch.set_facecolor('white')
fig.text(0.07, 0.955, '外来問診記録版 週次レポート', fontsize=20, weight='bold', color='#1a4d2e')
fig.text(0.07, 0.930, f'集計日: {DATE}    ／    登録件数: {n} 件', fontsize=11, color='#333333')
fig.text(0.07, 0.895, '【基本属性】', fontsize=12, weight='bold')
fig.text(0.10, 0.873, f'年齢: {mean:.1f} ± {sd:.1f}（範囲 {amin}–{amax}）', fontsize=11)
fig.text(0.10, 0.853, f'性別: 男性 {male}名 / 女性 {female}名', fontsize=11)
fig.text(0.10, 0.833, f'喫煙: 非喫煙 {smk["非喫煙"]}名 / 元喫煙 {smk["元喫煙"]}名 / 現喫煙 {smk["現喫煙"]}名', fontsize=11)
fig.text(0.07, 0.795, '【症状・曝露の有訴率】', fontsize=12, weight='bold')
sym = rate_list(SYMPTOMS)
fig.text(0.10, 0.773, ' ／ '.join(f'{l} {p:.0f}%({pos}/{tot})' for l, p, pos, tot in sym), fontsize=9.5)
fig.text(0.07, 0.725, '⚠ 架空のダミーデータ・集計のみ（個票は含みません／T26承認前）', fontsize=10, color='#b8860b')
ax = fig.add_axes([0.10, 0.52, 0.36, 0.12]); ax.hist(ages, bins=range(30, 95, 5), color='#5b8def', edgecolor='white')
ax.set_title('年齢分布', fontsize=11); ax.set_xlabel('年齢（歳）', fontsize=8); ax.set_ylabel('人数', fontsize=8); ax.tick_params(labelsize=8)
ax = fig.add_axes([0.58, 0.52, 0.36, 0.12]); ax.bar(['男性', '女性'], [male, female], color=['#5b8def', '#f08a7a'])
ax.set_title('性別', fontsize=11); ax.set_ylabel('人数', fontsize=8); ax.tick_params(labelsize=8)
ax = fig.add_axes([0.10, 0.30, 0.36, 0.12]); ax.bar(['非喫煙', '元喫煙', '現喫煙'], [smk['非喫煙'], smk['元喫煙'], smk['現喫煙']], color=['#5b8def', '#2f9e44', '#f08a7a'])
ax.set_title('喫煙状況', fontsize=11); ax.set_ylabel('人数', fontsize=8); ax.tick_params(labelsize=8)
ax = fig.add_axes([0.58, 0.30, 0.36, 0.12])
if smokers:
    labs = [s[0] for s in smokers][::-1]; vals = [s[1] for s in smokers][::-1]
    ax.barh(labs, vals, color='#f08a7a'); ax.set_xlabel('pack-years', fontsize=8)
    ax.set_title(f'喫煙者の pack-years（{len(smokers)}名）', fontsize=11); ax.tick_params(labelsize=8)
else:
    ax.axis('off'); ax.set_title('喫煙者の pack-years', fontsize=11)
ax = fig.add_axes([0.30, 0.075, 0.62, 0.12]); draw_barh(ax, sym, '#2f9e44', '症状・曝露の有訴率')
pp.savefig(fig); plt.close(fig)

# ===== P2 =====
fig = plt.figure(figsize=(8.27, 11.69), dpi=150); fig.patch.set_facecolor('white')
fig.text(0.07, 0.955, '曝露・既往プロファイル', fontsize=18, weight='bold', color='#1a4d2e')
fig.text(0.07, 0.930, '過敏性肺炎・職業性肺疾患・膠原病関連ILD のスクリーニング視点', fontsize=10.5, color='#555555')
ax = fig.add_axes([0.26, 0.52, 0.66, 0.33]); draw_barh(ax, rate_list(EXPO), '#2f9e44', '曝露プロファイル（環境・職業）')
ax = fig.add_axes([0.26, 0.08, 0.66, 0.38]); draw_barh(ax, rate_list(HISTORY), '#7048e8', '既往・アレルギー・自己免疫')
pp.savefig(fig); plt.close(fig)

# ===== P3 =====
fig = plt.figure(figsize=(8.27, 11.69), dpi=150); fig.patch.set_facecolor('white')
fig.text(0.07, 0.955, '家族歴・症例一覧', fontsize=18, weight='bold', color='#1a4d2e')
ax = fig.add_axes([0.30, 0.60, 0.62, 0.30]); draw_barh(ax, rate_list(FAMILY), '#e8912f', '家族歴（「あり」割合）')
ax = fig.add_axes([0.05, 0.06, 0.90, 0.42]); ax.axis('off')
ax.set_title('症例一覧（主要項目）', fontsize=13, weight='bold', loc='left')
cols = ['患者ID', '受診日', '年齢', '性別', '喫煙', '来院理由', '胸部症状']
cell = []
for d in data:
    sid = str(d.get('patient_id', '')).replace('ダミー ', '').split('（')[0]
    cell.append([sid, d.get('visit_date', '') or '', d.get('age', '') if d.get('age') is not None else '',
                 d.get('sex', '') or '', d.get('smoking_status', '') or '',
                 d.get('visit_reason', '') or '', d.get('chest_abnormality', '') or ''])
if cell:
    tbl = ax.table(cellText=cell, colLabels=cols, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(8); tbl.scale(1, 1.5)
    for j in range(len(cols)):
        tbl[0, j].set_facecolor('#2f855a'); tbl[0, j].set_text_props(color='white', weight='bold')
pp.savefig(fig); plt.close(fig)

pp.close()
print('SAVED report.pdf')
