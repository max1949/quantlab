-- ============================================================
-- QuantLab AI - PostgreSQL 初始化脚本
-- 在容器首次启动时由 docker-entrypoint-initdb.d 自动执行。
-- Sprint 1 阶段: 仅做数据库级基础设置 (扩展 / schema)。
-- 业务表结构由 Alembic 迁移管理, 不在此处建表 (避免与迁移冲突)。
-- ============================================================

-- UUID 生成 (主键采用 uuid)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 文本检索 / 模糊匹配 (后续排行榜、因子检索可能用到)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 业务 schema (与系统对象隔离)
CREATE SCHEMA IF NOT EXISTS quantlab AUTHORIZATION quantlab;

-- 默认搜索路径
ALTER DATABASE quantlab SET search_path TO quantlab, public;

-- 说明:
--   行情 K 线数据 (MarketData) V1 落地为 Parquet 文件,
--   PostgreSQL 仅保存数据索引 (品种 / 时间范围 / 文件路径),
--   该索引表同样由 Alembic 迁移创建。
