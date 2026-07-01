-- QuantLab cross-site card redemption: allow membership_redemptions for non-ai users

alter table public.membership_redemptions
  alter column user_id drop not null;

alter table public.membership_redemptions
  add column if not exists external_user_ref text;

create index if not exists idx_membership_redemptions_external
  on public.membership_redemptions(external_user_ref);
