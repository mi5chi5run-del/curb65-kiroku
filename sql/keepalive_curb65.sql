-- ============================================================
-- keepalive テーブル（CURB-65用Supabaseプロジェクト curb65-kiroku 専用）
--
-- 目的：無料プランの「7日間無活動で自動一時停止」を防ぐ番犬の書き込み先。
--       .github/workflows/keepalive.yml が1日2回ここへ upsert する。
--       CURB-65データ本体（curb65_records）を汚さないための専用1行テーブル。
--
-- ★問診用(sql/keepalive_monshin.sql)との違い：
--   このプロジェクトの publishable key は公開HTMLにも載っている＝誰でも叩ける。
--   そこでポリシーを「id = 1 の行だけ」に限定し、
--   第三者が行を無限に増やせないようにしてある。
--
-- 実行方法：Supabase ダッシュボード →（curb65-kiroku プロジェクト）→
--           SQL Editor → New query → 下を全部貼って Run。1回だけでよい。
-- 作成日：2026-08-14
-- ============================================================

create table if not exists public.keepalive (
  id        int primary key,
  last_ping timestamptz not null default now(),
  source    text
);

alter table public.keepalive enable row level security;

-- id = 1 の1行だけ、anon キーで読み書きできるようにする
-- （upsert には insert と update の両方のポリシーが要る）
drop policy if exists keepalive_anon_select on public.keepalive;
drop policy if exists keepalive_anon_insert on public.keepalive;
drop policy if exists keepalive_anon_update on public.keepalive;

create policy keepalive_anon_select on public.keepalive
  for select to anon using (id = 1);

create policy keepalive_anon_insert on public.keepalive
  for insert to anon with check (id = 1);

create policy keepalive_anon_update on public.keepalive
  for update to anon using (id = 1) with check (id = 1);

-- 初期行（id=1）を1本だけ用意する
insert into public.keepalive (id, last_ping, source)
values (1, now(), 'bootstrap')
on conflict (id) do nothing;

-- 確認用：1行だけ返ればOK
select * from public.keepalive;
