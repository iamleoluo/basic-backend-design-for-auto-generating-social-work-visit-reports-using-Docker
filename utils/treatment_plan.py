"""
處遇計畫模組
負責處理處遇計畫的動態配置生成、Prompt構建和相關業務邏輯
"""

import os
import json
import uuid
import sys
from .file_manager import file_manager


class TreatmentPlanManager:
    def __init__(self):
        # 案件類型對應的專業重點
        self.case_type_focus = {
            'family_mediation': '家事調解和衝突處理',
            'parent_child': '親子關係修復和溝通改善',
            'marriage_counseling': '婚姻關係諮商和伴侶治療',
            'child_protection': '兒童保護和安全評估',
            'domestic_violence': '家庭暴力防治和創傷復原',
            'other_family': '一般家庭問題處理'
        }
        
        # 服務領域對應的專業策略
        self.service_field_strategies = {
            'judicial_correction': '司法程序配合、法庭評估、矯治資源連結',
            'economic_assistance': '經濟扶助申請、就業輔導、理財規劃',
            'new_residents': '文化適應、語言學習、社區融入',
            'protection_services': '保護服務、風險評估、安全計畫',
            'children_youth': '兒少發展、教育支持、才能培養',
            'school_education': '學校合作、學習支援、特殊教育',
            'women_family': '婦女權益、家庭功能、性別議題',
            'medical_related': '醫療資源、復健服務、照護計畫',
            'psychological_mental': '心理治療、精神醫療、情緒支持',
            'disability': '身心障礙服務、輔具申請、無障礙環境',
            'elderly_longterm_care': '長照服務、老人照護、安養規劃'
        }
    
    def generate_treatment_plan_config(self, case_type: str, service_fields: list, custom_settings: dict) -> str:
        """根據參數動態生成處遇計畫配置文件"""
        
        try:
            # 讀取基礎處遇計畫配置
            base_config_file = 'treatment_plan.json' if os.path.exists('treatment_plan.json') else 'run.json'
            with open(base_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 構建動態處遇計畫prompt
            dynamic_prompt = self.build_treatment_plan_prompt(case_type, service_fields, custom_settings)
            
            # 修改配置中的template
            if 'steps' in config and len(config['steps']) > 0:
                config['steps'][0]['template'] = dynamic_prompt
                print(f"🔧 已生成客製化處遇計畫Prompt，長度: {len(dynamic_prompt)} 字元", file=sys.stderr)
            
            # 根據自定義設定調整參數
            if custom_settings:
                if 'style' in custom_settings:
                    config['temperature'] = file_manager.get_temperature_for_style(custom_settings['style'])
                    print(f"🌡️ 根據風格 '{custom_settings['style']}' 調整溫度: {config['temperature']}", file=sys.stderr)
            
            # 生成臨時配置文件
            temp_config_path = f"temp_treatment_config_{uuid.uuid4().hex[:8]}.json"
            with open(temp_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return temp_config_path
            
        except Exception as e:
            print(f"⚠️ 生成處遇計畫配置失敗: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 'treatment_plan.json' if os.path.exists('treatment_plan.json') else 'run.json'
    
    def build_treatment_plan_prompt(self, case_type: str, service_fields: list, custom_settings: dict) -> str:
        """構建動態處遇計畫prompt"""
        
        base_prompt = """你是一位專業的社會工作師，請根據以下社工報告，生成專業的處遇計畫。

處遇計畫應該包含以下結構：

一、處遇目標
(一)短期目標（1-3個月）
(二)中期目標（3-6個月）
(三)長期目標（6個月以上）

二、處遇策略
(一)個案工作策略
(二)家族治療策略
(三)資源連結策略
(四)環境調整策略

三、實施步驟
(一)評估階段
(二)介入階段
(三)維持階段
(四)結案評估

四、預期成效
(一)個人層面成效
(二)家庭層面成效
(三)社會功能改善
(四)風險降低程度

五、評估指標
(一)量化指標
(二)質化指標
(三)時程安排
(四)檢核方式

六、資源需求
(一)人力資源
(二)經費需求
(三)外部資源
(四)專業協助

撰寫要求：
- 請根據報告中的具體問題和需求制定切實可行的處遇計畫
- 目標設定應該具體、可測量、可達成
- 策略應該具有專業性和可操作性
- 時程安排要合理且具有彈性
- 充分考慮案主的能力、資源和限制
- 體現社會工作的專業價值和倫理"""
        
        # 根據案件類型調整重點
        if case_type and case_type in self.case_type_focus:
            focus = self.case_type_focus[case_type]
            base_prompt += f"\n\n特別重點：\n本案件為{focus}案件，請在處遇計畫中特別重視相關的專業介入策略和技巧。"
        
        # 根據服務領域調整策略建議
        if service_fields:
            selected_strategies = []
            for field in service_fields:
                if field in self.service_field_strategies:
                    selected_strategies.append(self.service_field_strategies[field])
            
            if selected_strategies:
                base_prompt += f"\n\n專業領域策略：\n請在處遇計畫中整合以下專業領域的策略和資源：\n- " + "\n- ".join(selected_strategies)
        
        # 添加自定義設定
        if custom_settings:
            if 'notes' in custom_settings and custom_settings['notes'].strip():
                base_prompt += f"\n\n特殊要求：\n{custom_settings['notes']}"
            
            if 'style' in custom_settings:
                style_instruction = self.get_treatment_plan_style_instruction(custom_settings['style'])
                base_prompt += f"\n\n撰寫風格：{style_instruction}"
        
        base_prompt += "\n\n請基於以下內容生成處遇計畫：\n\n{input}"
        
        return base_prompt
    
    def get_treatment_plan_style_instruction(self, style: str) -> str:
        """處遇計畫風格指令"""
        style_instructions = {
            'formal': '請使用正式、專業的語調，嚴格遵循社工實務標準，條理清晰地呈現每個處遇環節',
            'detailed': '請提供詳細、具體的處遇步驟，包含完整的實施細節、時程規劃和評估標準',
            'concise': '請保持簡潔有力，重點突出核心處遇策略和關鍵步驟，避免冗長描述'
        }
        return style_instructions.get(style, '請保持專業、實用的撰寫風格，確保處遇計畫具有可操作性')


# 全局處遇計畫管理器實例
treatment_plan_manager = TreatmentPlanManager()