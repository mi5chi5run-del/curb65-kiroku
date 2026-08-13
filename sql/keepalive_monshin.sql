-- ============================================================
-- keepalive テーブル（外来問診用Supabaseプロジェクト monshin-kiroku 専用）
--
-- 目的：無料プランの「7日間無活動で自動一時停止」を防ぐ番犬の書き込み先。
--       .github/workflows/keepalive-monshin.yml が1日2回ここへ upsert する。
--       問診データ本体（monshin_records）を汚さないための専用1行テーブル。
--
-- 実行方法：Supabase ダッシュボード →（monshin-kiroku プロジェクト）→
--           SQL Editor → New query → 下を全部貼って Run。1回だけでよい。
-- 作成日：2026-08-14
-- ============================================================

create table if not exists public.keepalive (
  id        int primary key,
  last_ping timestamptz not null default now(),
  source    text
);

alter table public.keepalive enable row level security;

-- このテーブルだけ anon キーで読み書きできるようにする
-- （upsert には insert と update の両方のポリシーが要る）
drop policy if exists keepalive_anon_select on public.keepalive;
drop policy if exists keepalive_anon_insert on public.keepalive;
drop policy if exists keepalive_anon_update on public.keepalive;

create policy keepalive_anon_select on public.keepalive
  for select to anon using (true);

create policy keepalive_anon_insert on public.keepalive
  for insert to anon with check (true);

create policy keepalive_anon_update on public.keepalive
  for update to anon using (true) with check (true);

-- 初期行（id=1）を1本だけ用意する
insert into public.keepalive (id, last_ping, source)
values (1, now(), 'bootstrap')
on conflict (id) do nothing;

-- 確認用：1行だけ返ればOK
select * from public.keepalive;
