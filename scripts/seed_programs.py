#!/usr/bin/env python3
"""
Seed the database with realistic CS program profiles and sample application cases.
Run: cd backend && python ../scripts/seed_programs.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
import app.models.user          # noqa
import app.models.document      # noqa
import app.models.knowledge     # noqa
import app.models.recommendation  # noqa
from app.models.knowledge import (
    ProgramProfile, ProgramType, EmploymentQuality, IndustryResources, ApplicationCase, CaseType,
)


# ─── Program seed data ────────────────────────────────────────────────────────
# Based on publicly available recruitment information from official university websites

PROGRAMS = [
    # ── 清华大学 ──────────────────────────────────────────────────────────────
    {
        "school": "清华大学", "department": "计算机科学与技术系",
        "direction": "人工智能", "program_type": "直博",
        "rank_threshold_hint": 0.05,  # roughly top 5%
        "school_tier_preference": ["985"],
        "research_weight": 0.9, "competition_weight": 0.4, "internship_weight": 0.3,
        "paper_requirement_hint": "顶会/CCF-A论文优先，一作发表更佳",
        "has_written_exam": False, "has_machine_test": True, "has_group_interview": False,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.TOP,
        "industry_resources": IndustryResources.RICH,
        "city": "北京", "profile_confidence": 0.85,
        "notes": "竞争极为激烈，强研究背景是核心要求",
    },
    {
        "school": "清华大学", "department": "软件学院",
        "direction": "软件工程", "program_type": "专硕",
        "rank_threshold_hint": 0.15,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.5, "competition_weight": 0.5, "internship_weight": 0.6,
        "has_written_exam": False, "has_machine_test": True, "has_group_interview": False,
        "phd_track_available": False,
        "avg_employment_quality": EmploymentQuality.TOP,
        "industry_resources": IndustryResources.RICH,
        "city": "北京", "profile_confidence": 0.80,
        "notes": "工程能力和ACM等竞赛背景受重视，学费较高",
    },
    # ── 北京大学 ──────────────────────────────────────────────────────────────
    {
        "school": "北京大学", "department": "计算机学院",
        "direction": "机器学习与人工智能", "program_type": "学硕",
        "rank_threshold_hint": 0.08,
        "school_tier_preference": ["985"],
        "research_weight": 0.85, "competition_weight": 0.3, "internship_weight": 0.2,
        "paper_requirement_hint": "有论文（在投或发表）竞争力显著提升",
        "has_written_exam": False, "has_machine_test": True, "has_group_interview": False,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.TOP,
        "industry_resources": IndustryResources.RICH,
        "city": "北京", "profile_confidence": 0.82,
    },
    {
        "school": "北京大学", "department": "信息科学技术学院",
        "direction": "计算机体系结构", "program_type": "学硕",
        "rank_threshold_hint": 0.10,
        "school_tier_preference": ["985"],
        "research_weight": 0.8, "competition_weight": 0.3, "internship_weight": 0.2,
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.TOP,
        "industry_resources": IndustryResources.RICH,
        "city": "北京", "profile_confidence": 0.78,
    },
    # ── 浙江大学 ──────────────────────────────────────────────────────────────
    {
        "school": "浙江大学", "department": "计算机科学与技术学院",
        "direction": "人工智能与数据挖掘", "program_type": "学硕",
        "rank_threshold_hint": 0.12,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.75, "competition_weight": 0.5, "internship_weight": 0.4,
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.TOP,
        "industry_resources": IndustryResources.RICH,
        "city": "杭州", "profile_confidence": 0.83,
        "notes": "杭州互联网产业资源丰富，阿里系实习机会多",
    },
    {
        "school": "浙江大学", "department": "软件学院",
        "direction": "软件工程", "program_type": "专硕",
        "rank_threshold_hint": 0.20,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.4, "competition_weight": 0.6, "internship_weight": 0.7,
        "has_machine_test": True,
        "phd_track_available": False,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.RICH,
        "city": "杭州", "profile_confidence": 0.80,
    },
    # ── 上海交通大学 ─────────────────────────────────────────────────────────
    {
        "school": "上海交通大学", "department": "计算机科学与工程系",
        "direction": "系统与网络", "program_type": "学硕",
        "rank_threshold_hint": 0.12,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.80, "competition_weight": 0.4, "internship_weight": 0.4,
        "paper_requirement_hint": "有科研产出者优先",
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.TOP,
        "industry_resources": IndustryResources.RICH,
        "city": "上海", "profile_confidence": 0.82,
        "notes": "上海优质实习资源丰富",
    },
    {
        "school": "上海交通大学", "department": "电子信息与电气工程学院",
        "direction": "人工智能", "program_type": "专硕",
        "rank_threshold_hint": 0.25,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.5, "competition_weight": 0.5, "internship_weight": 0.6,
        "has_machine_test": True,
        "phd_track_available": False,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.RICH,
        "city": "上海", "profile_confidence": 0.78,
    },
    # ── 中国科学院大学 ───────────────────────────────────────────────────────
    {
        "school": "中国科学院大学", "department": "计算技术研究所",
        "direction": "计算机体系结构", "program_type": "学硕",
        "rank_threshold_hint": 0.15,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.90, "competition_weight": 0.3, "internship_weight": 0.2,
        "paper_requirement_hint": "科研经历是最重要考量",
        "has_machine_test": False, "has_written_exam": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "北京", "profile_confidence": 0.75,
        "notes": "科研属于中科院体制，学术氛围浓厚，导师差异大",
    },
    {
        "school": "中国科学院大学", "department": "软件研究所",
        "direction": "软件工程与系统", "program_type": "学硕",
        "rank_threshold_hint": 0.20,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.85, "competition_weight": 0.25,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "北京", "profile_confidence": 0.72,
    },
    # ── 哈尔滨工业大学 ───────────────────────────────────────────────────────
    {
        "school": "哈尔滨工业大学", "department": "计算机科学与技术学院",
        "direction": "人工智能", "program_type": "学硕",
        "rank_threshold_hint": 0.18,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.75, "competition_weight": 0.4,
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "哈尔滨", "profile_confidence": 0.78,
        "notes": "也有深圳校区，就业资源更好",
    },
    {
        "school": "哈尔滨工业大学（深圳）", "department": "计算机科学与技术学院",
        "direction": "人工智能与大数据", "program_type": "专硕",
        "rank_threshold_hint": 0.25,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.55, "competition_weight": 0.5, "internship_weight": 0.65,
        "has_machine_test": True,
        "phd_track_available": False,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.RICH,
        "city": "深圳", "profile_confidence": 0.80,
        "notes": "深圳校区招生竞争激烈，互联网实习机会多",
    },
    # ── 南京大学 ─────────────────────────────────────────────────────────────
    {
        "school": "南京大学", "department": "计算机科学与技术系",
        "direction": "机器学习", "program_type": "学硕",
        "rank_threshold_hint": 0.15,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.80, "competition_weight": 0.35,
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "南京", "profile_confidence": 0.80,
    },
    # ── 北京航空航天大学 ─────────────────────────────────────────────────────
    {
        "school": "北京航空航天大学", "department": "计算机学院",
        "direction": "网络空间安全", "program_type": "学硕",
        "rank_threshold_hint": 0.20,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.70, "competition_weight": 0.50,
        "has_machine_test": False, "has_written_exam": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "北京", "profile_confidence": 0.76,
        "notes": "信安竞赛（CTF等）背景受重视",
    },
    {
        "school": "北京航空航天大学", "department": "软件学院",
        "direction": "软件工程", "program_type": "专硕",
        "rank_threshold_hint": 0.30,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.40, "competition_weight": 0.45, "internship_weight": 0.60,
        "has_machine_test": True,
        "phd_track_available": False,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "北京", "profile_confidence": 0.73,
    },
    # ── 复旦大学 ─────────────────────────────────────────────────────────────
    {
        "school": "复旦大学", "department": "计算机科学技术学院",
        "direction": "自然语言处理", "program_type": "学硕",
        "rank_threshold_hint": 0.15,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.80, "competition_weight": 0.35,
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.TOP,
        "industry_resources": IndustryResources.RICH,
        "city": "上海", "profile_confidence": 0.79,
    },
    # ── 中国科学技术大学 ─────────────────────────────────────────────────────
    {
        "school": "中国科学技术大学", "department": "计算机科学与技术学院",
        "direction": "人工智能", "program_type": "学硕",
        "rank_threshold_hint": 0.12,
        "school_tier_preference": ["985"],
        "research_weight": 0.85, "competition_weight": 0.35,
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "合肥", "profile_confidence": 0.78,
        "notes": "学术氛围好，科研要求高",
    },
    # ── 华中科技大学 ─────────────────────────────────────────────────────────
    {
        "school": "华中科技大学", "department": "计算机科学与技术学院",
        "direction": "大数据与云计算", "program_type": "学硕",
        "rank_threshold_hint": 0.25,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.65, "competition_weight": 0.45,
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "武汉", "profile_confidence": 0.75,
    },
    # ── 同济大学 ─────────────────────────────────────────────────────────────
    {
        "school": "同济大学", "department": "计算机科学与技术学院",
        "direction": "人工智能", "program_type": "专硕",
        "rank_threshold_hint": 0.30,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.50, "competition_weight": 0.50, "internship_weight": 0.65,
        "has_machine_test": True,
        "phd_track_available": False,
        "avg_employment_quality": EmploymentQuality.EXCELLENT,
        "industry_resources": IndustryResources.RICH,
        "city": "上海", "profile_confidence": 0.73,
    },
    # ── 电子科技大学 ─────────────────────────────────────────────────────────
    {
        "school": "电子科技大学", "department": "计算机科学与工程学院",
        "direction": "网络空间安全", "program_type": "学硕",
        "rank_threshold_hint": 0.30,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.65, "competition_weight": 0.55,
        "has_machine_test": False, "has_written_exam": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.GOOD,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "成都", "profile_confidence": 0.72,
    },
    # ── 北京理工大学 ─────────────────────────────────────────────────────────
    {
        "school": "北京理工大学", "department": "计算机学院",
        "direction": "计算机科学与技术", "program_type": "学硕",
        "rank_threshold_hint": 0.30,
        "school_tier_preference": ["985", "211"],
        "research_weight": 0.65, "competition_weight": 0.40,
        "has_machine_test": True,
        "phd_track_available": True,
        "avg_employment_quality": EmploymentQuality.GOOD,
        "industry_resources": IndustryResources.AVERAGE,
        "city": "北京", "profile_confidence": 0.70,
    },
]

# ─── Sample application cases (anonymized) ────────────────────────────────────
SAMPLE_CASES = [
    # Successful cases
    {
        "applicant_school": "武汉大学", "applicant_school_tier": "985",
        "applicant_major": "计算机科学", "applicant_gpa_percentile": 0.35,
        "applicant_rank_percentile": 0.08, "applicant_has_paper": True,
        "applicant_paper_level": "CCF-B", "applicant_competition_level": "国家",
        "applicant_has_internship": True, "applicant_research_months": 12,
        "target_school": "清华大学", "target_department": "计算机科学与技术系",
        "target_direction": "人工智能", "target_program_type": "直博",
        "application_year": 2025, "got_camp_invite": True,
        "camp_result": "优营", "final_offer": True, "final_decision": "接受",
        "case_type": "success", "credibility": 0.7, "is_verified": False,
    },
    {
        "applicant_school": "中国人民大学", "applicant_school_tier": "211",
        "applicant_major": "软件工程", "applicant_rank_percentile": 0.05,
        "applicant_has_paper": True, "applicant_paper_level": "CCF-A",
        "applicant_competition_level": "国际", "applicant_has_internship": False,
        "applicant_research_months": 18,
        "target_school": "清华大学", "target_department": "软件学院",
        "target_direction": "软件工程", "target_program_type": "专硕",
        "application_year": 2025, "got_camp_invite": True,
        "camp_result": "录取", "final_offer": True, "final_decision": "接受",
        "case_type": "success", "credibility": 0.65,
    },
    {
        "applicant_school": "华中科技大学", "applicant_school_tier": "985",
        "applicant_major": "计算机", "applicant_rank_percentile": 0.12,
        "applicant_has_paper": False, "applicant_competition_level": "国家",
        "applicant_has_internship": True, "applicant_research_months": 8,
        "target_school": "浙江大学", "target_department": "计算机科学与技术学院",
        "target_direction": "人工智能与数据挖掘", "target_program_type": "学硕",
        "application_year": 2025, "got_camp_invite": True,
        "camp_result": "优营", "final_offer": True, "final_decision": "接受",
        "case_type": "success", "credibility": 0.6,
    },
    {
        "applicant_school": "北京邮电大学", "applicant_school_tier": "211",
        "applicant_major": "计算机", "applicant_rank_percentile": 0.03,
        "applicant_has_paper": True, "applicant_paper_level": "CCF-B",
        "applicant_competition_level": "国家",
        "applicant_has_internship": True, "applicant_research_months": 15,
        "target_school": "北京大学", "target_department": "计算机学院",
        "target_direction": "机器学习与人工智能", "target_program_type": "学硕",
        "application_year": 2024, "got_camp_invite": True,
        "camp_result": "优营", "final_offer": True, "final_decision": "接受",
        "case_type": "success", "credibility": 0.65,
    },
    {
        "applicant_school": "南京大学", "applicant_school_tier": "985",
        "applicant_major": "软件工程", "applicant_rank_percentile": 0.15,
        "applicant_has_paper": False, "applicant_competition_level": "省级",
        "applicant_has_internship": True, "applicant_research_months": 6,
        "target_school": "上海交通大学", "target_department": "电子信息与电气工程学院",
        "target_direction": "人工智能", "target_program_type": "专硕",
        "application_year": 2025, "got_camp_invite": True,
        "camp_result": "录取", "final_offer": True, "final_decision": "接受",
        "case_type": "success", "credibility": 0.6,
    },
    # Partial/failure cases (gives realistic picture)
    {
        "applicant_school": "中山大学", "applicant_school_tier": "985",
        "applicant_major": "计算机科学", "applicant_rank_percentile": 0.25,
        "applicant_has_paper": False, "applicant_competition_level": "省级",
        "applicant_has_internship": False, "applicant_research_months": 3,
        "target_school": "清华大学", "target_department": "计算机科学与技术系",
        "target_direction": "人工智能", "target_program_type": "直博",
        "application_year": 2025, "got_camp_invite": True,
        "camp_result": "淘汰", "final_offer": False,
        "case_type": "failure", "credibility": 0.5,
    },
    {
        "applicant_school": "西安电子科技大学", "applicant_school_tier": "211",
        "applicant_major": "计算机", "applicant_rank_percentile": 0.05,
        "applicant_has_paper": False, "applicant_competition_level": "国家",
        "applicant_has_internship": True, "applicant_research_months": 6,
        "target_school": "浙江大学", "target_department": "计算机科学与技术学院",
        "target_direction": "人工智能与数据挖掘",
        "application_year": 2024, "got_camp_invite": True,
        "camp_result": "候补", "final_offer": None,
        "case_type": "partial", "credibility": 0.55,
    },
    {
        "applicant_school": "哈尔滨工业大学", "applicant_school_tier": "985",
        "applicant_major": "计算机", "applicant_rank_percentile": 0.20,
        "applicant_has_paper": False, "applicant_competition_level": None,
        "applicant_has_internship": True, "applicant_research_months": 4,
        "target_school": "哈尔滨工业大学（深圳）",
        "target_department": "计算机科学与技术学院",
        "target_direction": "人工智能与大数据",
        "application_year": 2025, "got_camp_invite": True,
        "camp_result": "录取", "final_offer": True, "final_decision": "接受",
        "case_type": "success", "credibility": 0.6,
    },
    {
        "applicant_school": "北京科技大学", "applicant_school_tier": "211",
        "applicant_major": "软件工程", "applicant_rank_percentile": 0.08,
        "applicant_has_paper": True, "applicant_paper_level": "CCF-C",
        "applicant_has_internship": True, "applicant_research_months": 9,
        "target_school": "华中科技大学",
        "target_department": "计算机科学与技术学院",
        "target_direction": "大数据与云计算",
        "application_year": 2025, "got_camp_invite": True,
        "camp_result": "优营", "final_offer": True, "final_decision": "接受",
        "case_type": "success", "credibility": 0.6,
    },
    {
        "applicant_school": "湖南大学", "applicant_school_tier": "211",
        "applicant_major": "计算机", "applicant_rank_percentile": 0.12,
        "applicant_has_paper": False, "applicant_competition_level": "国家",
        "applicant_has_internship": True, "applicant_research_months": 6,
        "target_school": "南京大学",
        "target_department": "计算机科学与技术系",
        "target_direction": "机器学习",
        "application_year": 2024, "got_camp_invite": True,
        "camp_result": "录取", "final_offer": True, "final_decision": "接受",
        "case_type": "success", "credibility": 0.55,
    },
]


async def seed():
    """Create tables and seed data."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Seeding program profiles...")
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(ProgramProfile))
        count = result.scalar()
        if count and count > 0:
            print(f"Found {count} existing programs. Skipping seed.")
        else:
            for prog_data in PROGRAMS:
                program_type_str = prog_data.pop("program_type")
                profile_confidence = prog_data.pop("profile_confidence", 0.75)
                try:
                    pt = ProgramType(program_type_str)
                except ValueError:
                    print(f"Invalid program type: {program_type_str}")
                    continue

                canonical = f"{prog_data['school']}-{prog_data['department']}-{prog_data['direction']}-{pt.value}"
                program = ProgramProfile(
                    program_type=pt,
                    canonical_name=canonical,
                    evidence_count=3,
                    profile_confidence=profile_confidence,
                    **prog_data,
                )
                db.add(program)

            print(f"Added {len(PROGRAMS)} program profiles")

        # Seed cases
        result = await db.execute(select(func.count()).select_from(ApplicationCase))
        case_count = result.scalar()
        if case_count and case_count > 0:
            print(f"Found {case_count} existing cases. Skipping case seed.")
        else:
            from app.models.knowledge import CampResult, FinalDecision
            for case_data in SAMPLE_CASES:
                camp_result_str = case_data.pop("camp_result", None)
                final_decision_str = case_data.pop("final_decision", None)
                case_type_str = case_data.pop("case_type")

                case = ApplicationCase(
                    **case_data,
                    camp_result=CampResult(camp_result_str) if camp_result_str else None,
                    final_decision=FinalDecision(final_decision_str) if final_decision_str else None,
                    case_type=CaseType(case_type_str),
                )
                db.add(case)

            print(f"Added {len(SAMPLE_CASES)} application cases")

        await db.commit()

    print("✓ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
