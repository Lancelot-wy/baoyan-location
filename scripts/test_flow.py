#!/usr/bin/env python3
"""
End-to-end test: creates a student profile, triggers recommendations, prints results.
Run: cd backend && python ../scripts/test_flow.py
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


async def test_full_flow():
    from app.db.session import AsyncSessionLocal, engine
    from app.db.base import Base
    import app.models.user
    import app.models.document
    import app.models.knowledge
    import app.models.recommendation
    from app.models.user import (
        UserProfile, ResearchExperience, Paper, Competition, Internship, PreferenceProfile,
        SchoolTier, MajorCategory, CurrentYear, EnglishReadingLevel, ResearchOrientation,
        UserRole, VenueLevel, PaperStatus, CompetitionCategory, CompetitionLevel,
        CompetitionAward, Relevance, CareerGoal, RiskAppetite,
    )
    from app.services.recommendation.profile_builder import build_student_tags
    from app.services.recommendation.program_ranker import rank_programs
    from app.services.recommendation.evidence_aggregator import aggregate_evidence_for_program
    from app.services.recommendation.explanation_generator import generate_profile_summary, generate_explanation
    from datetime import date
    import uuid

    # Ensure tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("=" * 60)
    print("保研推免定位器 — 端到端测试")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # Create test student: 211院校，专业前10%，有一篇CCF-B论文
        print("\n[1] 创建测试学生档案...")
        profile = UserProfile(
            session_id=str(uuid.uuid4()),
            undergraduate_school="北京邮电大学",
            school_tier=SchoolTier.S211,
            major_name="计算机科学与技术",
            major_category=MajorCategory.CS,
            current_year=CurrentYear.THIRD,
            has_guaranteed_admission=False,
            gpa=3.7,
            gpa_full=4.0,
            major_rank=8,
            major_rank_total=80,
            rank_percentile=0.10,
            has_disciplinary_issues=False,
            cet6_score=530,
            english_reading_level=EnglishReadingLevel.CAN_READ,
            research_orientation=ResearchOrientation.RESEARCH,
        )
        db.add(profile)
        await db.flush()

        # Research experience
        exp = ResearchExperience(
            user_id=profile.id,
            start_date=date(2024, 3, 1),
            advisor_name="张三",
            advisor_title="副教授",
            advisor_institution="北京邮电大学",
            research_direction="自然语言处理",
            is_long_term=True,
            user_role=UserRole.MODULE,
            has_advisor_endorsement=True,
        )
        db.add(exp)

        # Paper
        paper = Paper(
            user_id=profile.id,
            title="基于大语言模型的文本分类方法研究",
            venue="ACL Findings 2025",
            venue_level=VenueLevel.CCF_A,
            status=PaperStatus.UNDER_REVIEW,
            author_position=2,
            total_authors=4,
            is_first_author=False,
            research_direction="自然语言处理",
            actual_contribution="负责实验设计和主要代码实现",
            has_open_source=True,
            year=2025,
        )
        db.add(paper)

        # Competition
        comp = Competition(
            user_id=profile.id,
            name="2024年全国大学生数学建模竞赛",
            category=CompetitionCategory.MATH_MODEL,
            level=CompetitionLevel.NATIONAL,
            award=CompetitionAward.SECOND,
            is_team=True,
            team_size=3,
            relevance_to_application=Relevance.PARTIAL,
            year=2024,
        )
        db.add(comp)

        # Preferences
        pref = PreferenceProfile(
            user_id=profile.id,
            career_goal=CareerGoal.EMPLOYMENT,
            risk_appetite=RiskAppetite.BALANCED,
            accept_high_pressure_advisor=False,
            prioritize_city=True,
            prioritize_school_brand=True,
            prioritize_internship_resources=True,
            prioritize_phd_track=False,
            accept_cross_direction=False,
            preferred_cities=["北京", "上海", "深圳", "杭州"],
            excluded_cities=[],
            target_directions=["自然语言处理", "机器学习"],
        )
        db.add(pref)
        await db.flush()

        print(f"  学生ID: {profile.session_id}")
        print(f"  学校: {profile.undergraduate_school} ({profile.school_tier.value})")
        print(f"  排名: {profile.major_rank}/{profile.major_rank_total} (前{profile.rank_percentile*100:.1f}%)")
        print(f"  论文: CCF-A在投，二作")
        print(f"  竞赛: 全国数学建模二等奖")

        # Build student tags
        print("\n[2] 构建学生画像...")
        tags = build_student_tags(
            profile=profile,
            research_experiences=[exp],
            papers=[paper],
            competitions=[comp],
            internships=[],
            preferences=pref,
        )
        print(f"  综合实力评分: {tags.overall_strength}/100")
        print(f"  科研强度: {tags.research_strength}")
        print(f"  论文强度: {tags.paper_strength} ({tags.best_paper_level})")
        print(f"  竞赛强度: {tags.competition_strength}")

        # Generate profile summary
        print("\n[3] 生成个人画像分析...")
        summary = await generate_profile_summary(tags)
        print(f"  总体评估: {summary.get('overall_assessment', 'N/A')}")
        print(f"  核心优势:")
        for s in summary.get("core_strengths", [])[:3]:
            print(f"    • {s}")
        print(f"  核心短板:")
        for w in summary.get("core_weaknesses", [])[:3]:
            print(f"    • {w}")

        # Rank programs
        print("\n[4] 检索匹配院校项目...")
        from sqlalchemy import select, func
        from app.models.knowledge import ProgramProfile as PP
        result = await db.execute(select(func.count()).select_from(PP))
        prog_count = result.scalar()
        print(f"  知识库中共 {prog_count} 个项目")

        scored_programs = await rank_programs(db=db, tags=tags, top_n=10)
        print(f"  推荐结果: {len(scored_programs)} 个项目")

        if not scored_programs:
            print("  ⚠️  没有找到匹配项目，请先运行 scripts/seed_programs.py")
            await db.rollback()
            return

        print("\n[5] 推荐结果（按层级）:\n")

        tiers = {"冲刺": [], "主申": [], "保底": []}
        for s in scored_programs:
            tiers[s.tier].append(s)

        for tier_name, items in tiers.items():
            if not items:
                continue
            print(f"  ── {tier_name} ({'🔥' if tier_name == '冲刺' else '⭐' if tier_name == '主申' else '🛡️'}) ──")
            for scored in items[:4]:
                prob = f"{scored.admission_prob_low*100:.0f}%-{scored.admission_prob_high*100:.0f}%"
                print(f"    [{scored.compatibility_score:.1f}分] {scored.program.school} · "
                      f"{scored.program.department} · {scored.program.program_type.value}")
                print(f"           录取概率: {prob} | 城市: {scored.program.city or '未知'}")

        # Detailed look at top recommendation
        top = scored_programs[0]
        print(f"\n[6] 第一推荐详情: {top.program.school} - {top.program.department}")
        evidence = await aggregate_evidence_for_program(
            db=db,
            school=top.program.school,
            department=top.program.department,
        )
        explanation = await generate_explanation(tags, top, evidence)
        print(f"  推荐理由: {explanation.get('evidence_summary', 'N/A')[:200]}")
        print(f"  主要风险: {explanation.get('risk_summary', 'N/A')[:200]}")
        print(f"  准备建议: {explanation.get('preparation_advice', 'N/A')[:300]}")

        await db.rollback()  # Don't persist test data

    print("\n✅ 测试完成！系统端到端流程正常。")


if __name__ == "__main__":
    asyncio.run(test_full_flow())
