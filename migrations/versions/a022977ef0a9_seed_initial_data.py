"""seed initial data — 系统角色、权限矩阵、默认租户

Revision ID: a022977ef0a9
Revises: d46e1da4110b
Create Date: 2026-04-04

"""
from alembic import op
import sqlalchemy as sa


revision: str = 'a022977ef0a9'
down_revision = 'd46e1da4110b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 系统角色
    op.execute("""
        INSERT INTO roles (id, name, display_name, description, level, is_system) VALUES
        ('super_admin', 'super_admin', '超级管理员', '管理所有机构', 0, true),
        ('org_admin',   'org_admin',   '机构管理员', '管理本机构所有校区', 1, true),
        ('campus_admin','campus_admin','校区管理员', '管理本校区', 2, true),
        ('teacher',     'teacher',     '教师',      '使用PPT软件', 2, true)
        ON CONFLICT (id) DO NOTHING;
    """)

    # 2. 权限
    op.execute("""
        INSERT INTO permissions (id, resource, action, display_name, description) VALUES
        ('user:create',    'user',      'create', '创建用户',   ''),
        ('user:read',      'user',      'read',   '查看用户',   ''),
        ('user:update',    'user',      'update', '更新用户',   ''),
        ('user:delete',    'user',      'delete', '删除用户',   ''),
        ('campus:create',  'campus',    'create', '创建校区',   ''),
        ('campus:read',    'campus',    'read',   '查看校区',   ''),
        ('campus:update',  'campus',    'update', '更新校区',   ''),
        ('campus:delete',  'campus',    'delete', '删除校区',   ''),
        ('role:create',    'role',      'create', '创建角色',   ''),
        ('role:read',      'role',      'read',   '查看角色',   ''),
        ('role:update',    'role',      'update', '更新角色',   ''),
        ('role:delete',    'role',      'delete', '删除角色',   ''),
        ('app:create',     'app',       'create', '注册应用',   ''),
        ('app:read',       'app',       'read',   '查看应用',   ''),
        ('app:update',     'app',       'update', '更新应用',   ''),
        ('analytics:read', 'analytics', 'read',   '查看统计',   ''),
        ('config:read',    'config',    'read',   '查看配置',   ''),
        ('config:update',  'config',    'update', '更新配置',   '')
        ON CONFLICT (id) DO NOTHING;
    """)

    # 3. 角色-权限关联
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id) VALUES
        ('super_admin', 'user:create'),    ('super_admin', 'user:read'),
        ('super_admin', 'user:update'),    ('super_admin', 'user:delete'),
        ('super_admin', 'campus:create'),  ('super_admin', 'campus:read'),
        ('super_admin', 'campus:update'),  ('super_admin', 'campus:delete'),
        ('super_admin', 'role:create'),    ('super_admin', 'role:read'),
        ('super_admin', 'role:update'),    ('super_admin', 'role:delete'),
        ('super_admin', 'app:create'),     ('super_admin', 'app:read'),
        ('super_admin', 'app:update'),     ('super_admin', 'analytics:read'),
        ('super_admin', 'config:read'),    ('super_admin', 'config:update'),
        ('org_admin', 'user:create'),      ('org_admin', 'user:read'),
        ('org_admin', 'user:update'),      ('org_admin', 'user:delete'),
        ('org_admin', 'campus:create'),    ('org_admin', 'campus:read'),
        ('org_admin', 'campus:update'),    ('org_admin', 'campus:delete'),
        ('org_admin', 'analytics:read'),   ('org_admin', 'config:read'),
        ('campus_admin', 'user:create'),   ('campus_admin', 'user:read'),
        ('campus_admin', 'user:update'),   ('campus_admin', 'user:delete'),
        ('campus_admin', 'campus:read'),   ('campus_admin', 'analytics:read'),
        ('teacher', 'user:read')
        ON CONFLICT DO NOTHING;
    """)

    # 4. 默认租户
    op.execute("""
        INSERT INTO tenants (id, name, tenant_id, status)
        VALUES ('default', '法贝实验室', 'default', 'active')
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("DELETE FROM role_permissions WHERE role_id IN ('super_admin','org_admin','campus_admin','teacher')")
    op.execute("DELETE FROM permissions WHERE resource IN ('user','campus','role','app','analytics','config')")
    op.execute("DELETE FROM roles WHERE id IN ('super_admin','org_admin','campus_admin','teacher')")
    op.execute("DELETE FROM tenants WHERE id = 'default'")
