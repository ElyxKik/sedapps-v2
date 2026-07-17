"""Backfill credit transactions from completed AI jobs.

Revision ID: 0006_backfill_credit_ledger
Revises: 0005_credit_ledger
"""

from alembic import op

revision = "0006_backfill_credit_ledger"
down_revision = "0005_credit_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE ai_jobs AS job
        SET initiated_by_user_id = (
            SELECT membership.user_id
            FROM memberships AS membership
            WHERE membership.org_id = job.tenant_id
            ORDER BY
                CASE WHEN membership.role = 'owner' THEN 0 ELSE 1 END,
                membership.created_at
            LIMIT 1
        )
        WHERE job.initiated_by_user_id IS NULL
        """
    )
    op.execute(
        """
        WITH missing AS (
            SELECT
                job.tenant_id,
                SUM((job.tokens_in + job.tokens_out + 999) / 1000)::integer AS credits
            FROM ai_jobs AS job
            WHERE job.tokens_in + job.tokens_out > 0
              AND job.finished_at >= date_trunc('month', now())
              AND NOT EXISTS (
                  SELECT 1 FROM credit_transactions AS tx WHERE tx.job_id = job.id
              )
            GROUP BY job.tenant_id
        ), quota AS (
            SELECT
                organization.id,
                organization.ai_credits_used AS old_used,
                organization.ai_bonus_credits AS old_bonus,
                missing.credits,
                CASE organization.plan
                    WHEN 'starter' THEN 2500
                    WHEN 'pro' THEN 10000
                    WHEN 'business' THEN 50000
                    ELSE 500
                END AS plan_quota
            FROM organizations AS organization
            JOIN missing ON missing.tenant_id = organization.id
        )
        UPDATE organizations AS organization
        SET
            ai_credits_used = quota.old_used + quota.credits,
            ai_bonus_credits = GREATEST(
                0,
                quota.old_bonus - (
                    GREATEST(0, quota.old_used + quota.credits - quota.plan_quota)
                    - GREATEST(0, quota.old_used - quota.plan_quota)
                )
            )
        FROM quota
        WHERE organization.id = quota.id
        """
    )
    op.execute(
        """
        INSERT INTO credit_transactions (
            id, tenant_id, user_id, job_id, type, credits_delta,
            balance_after, tokens_in, tokens_out, operation, description,
            meta, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            job.tenant_id,
            job.initiated_by_user_id,
            job.id,
            'consumption',
            -((job.tokens_in + job.tokens_out + 999) / 1000)::integer,
            GREATEST(
                0,
                CASE organization.plan
                    WHEN 'starter' THEN 2500
                    WHEN 'pro' THEN 10000
                    WHEN 'business' THEN 50000
                    ELSE 500
                END
                + organization.ai_bonus_credits
                - organization.ai_credits_used
                - organization.ai_credits_reserved
            ),
            job.tokens_in,
            job.tokens_out,
            job.workflow,
            'Reprise historique : ' || job.workflow,
            '{"source":"migration_0006"}'::jsonb,
            COALESCE(job.finished_at, job.created_at),
            now()
        FROM ai_jobs AS job
        JOIN organizations AS organization ON organization.id = job.tenant_id
        WHERE job.tokens_in + job.tokens_out > 0
          AND NOT EXISTS (
              SELECT 1 FROM credit_transactions AS tx WHERE tx.job_id = job.id
          )
        """
    )
    op.execute(
        """
        UPDATE ai_jobs AS job
        SET
            charged_credits = ((job.tokens_in + job.tokens_out + 999) / 1000)::integer,
            credits_settled = true
        WHERE job.tokens_in + job.tokens_out > 0
          AND EXISTS (
              SELECT 1
              FROM credit_transactions AS tx
              WHERE tx.job_id = job.id
                AND tx.meta->>'source' = 'migration_0006'
          )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        WITH backfilled AS (
            SELECT tenant_id, SUM(-credits_delta)::integer AS credits
            FROM credit_transactions
            WHERE meta->>'source' = 'migration_0006'
              AND created_at >= date_trunc('month', now())
            GROUP BY tenant_id
        )
        UPDATE organizations AS organization
        SET ai_credits_used = GREATEST(0, organization.ai_credits_used - backfilled.credits)
        FROM backfilled
        WHERE organization.id = backfilled.tenant_id
        """
    )
    op.execute(
        """
        UPDATE ai_jobs AS job
        SET charged_credits = 0, credits_settled = false
        WHERE EXISTS (
            SELECT 1
            FROM credit_transactions AS tx
            WHERE tx.job_id = job.id
              AND tx.meta->>'source' = 'migration_0006'
        )
        """
    )
    op.execute(
        "DELETE FROM credit_transactions WHERE meta->>'source' = 'migration_0006'"
    )
