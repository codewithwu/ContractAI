import os
import re
from docx import Document
from typing import List, Dict, Any

class ContractParser:
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx']
        # 主条款模式（只匹配主条款标题）
        self.main_clause_patterns = [
            r'^第[一二三四五六七八九十零]+条',  # 中文主条款
            r'^第\d+条',  # 数字主条款
            r'^ARTICLE',  # 英文主条款
            r'^SECTION',  # 英文章节
        ]
        # 子条款模式
        self.sub_clause_patterns = [
            r'^\d+\.\d+',  # 1.1, 2.3 等子条款
            r'^[一二三四五六七八九十]、',  # 中文编号
            r'^\d+、',  # 数字编号
        ]
    
    def load_contract(self, file_path: str) -> List[Dict[str, Any]]:
        """加载合同文件并提取文本内容"""
        try:
            doc = Document(file_path)
            content = []
            
            # 提取所有段落
            for i, paragraph in enumerate(doc.paragraphs):
                text = paragraph.text.strip()
                if text:
                    content.append({
                        'page_content': text,
                        'metadata': {
                            'source': file_path,
                            'paragraph_id': i,
                            'type': 'paragraph'
                        }
                    })
            
            return content
            
        except Exception as e:
            raise Exception(f"解析Word文档失败: {str(e)}")
    
    def split_into_clauses(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """智能条款分割 - 将子条款合并到主条款中"""
        clauses = []
        current_main_clause = []
        current_main_title = "合同前言"
        current_sub_clauses = []
        
        for doc in documents:
            text = doc['page_content']
            metadata = doc['metadata']
            
            # 检查是否是主条款标题
            is_main_clause = self._is_main_clause(text)
            is_sub_clause = self._is_sub_clause(text)
            
            if is_main_clause:
                # 保存上一个主条款及其子条款
                if current_main_clause or current_sub_clauses:
                    full_content = self._combine_clause_content(current_main_clause, current_sub_clauses)
                    clauses.append({
                        'page_content': full_content,
                        'metadata': {
                            **metadata,
                            'clause_title': current_main_title,
                            'type': 'main_clause',
                            'sub_clause_count': len(current_sub_clauses)
                        }
                    })
                
                # 开始新的主条款
                current_main_clause = [text]
                current_main_title = text
                current_sub_clauses = []
                
            elif is_sub_clause:
                # 添加到子条款列表
                current_sub_clauses.append(text)
            else:
                # 普通内容，添加到当前主条款或子条款
                if current_sub_clauses:
                    # 如果有子条款，添加到最后一个子条款
                    if current_sub_clauses:
                        current_sub_clauses[-1] += "\n" + text
                else:
                    current_main_clause.append(text)
        
        # 添加最后一个条款
        if current_main_clause or current_sub_clauses:
            full_content = self._combine_clause_content(current_main_clause, current_sub_clauses)
            clauses.append({
                'page_content': full_content,
                'metadata': {
                    **metadata,
                    'clause_title': current_main_title,
                    'type': 'main_clause',
                    'sub_clause_count': len(current_sub_clauses)
                }
            })
        
        return clauses
    
    def _is_main_clause(self, text: str) -> bool:
        """判断是否为主条款标题"""
        for pattern in self.main_clause_patterns:
            if re.match(pattern, text.strip()):
                return True
        return False
    
    def _is_sub_clause(self, text: str) -> bool:
        """判断是否为子条款"""
        for pattern in self.sub_clause_patterns:
            if re.match(pattern, text.strip()):
                return True
        return False
    
    def _combine_clause_content(self, main_clause: List[str], sub_clauses: List[str]) -> str:
        """合并主条款和子条款内容"""
        content_parts = []
        
        # 添加主条款内容
        if main_clause:
            content_parts.extend(main_clause)
        
        # 添加子条款内容
        if sub_clauses:
            content_parts.extend(sub_clauses)
        
        return '\n'.join(content_parts)
    
    def analyze_risks(self, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析每个条款的风险"""
        risk_keywords = {
            '财务风险': ['支付', '付款', '违约金', '价格', '金额', '赔偿', '利息'],
            '交付风险': ['交付', '验收', '标准', '时间', '期限', '延迟', '尽快'],
            '法律风险': ['争议', '诉讼', '管辖', '知识产权', '保密', '责任'],
            '模糊条款': ['适当', '合理', '相关', '通用标准', '协商解决', '行业标准'],
            '不平等条款': ['单方', '甲方所在地', '乙方承担全部责任']
        }
        
        analyzed_clauses = []
        
        for clause in clauses:
            content = clause['page_content']
            risks_found = []
            
            for risk_type, keywords in risk_keywords.items():
                if any(keyword in content for keyword in keywords):
                    risks_found.append(risk_type)
            
            # 计算风险等级
            risk_level = "低风险"
            if len(risks_found) >= 3:
                risk_level = "高风险"
            elif len(risks_found) >= 1:
                risk_level = "中风险"
            
            analyzed_clauses.append({
                **clause,
                'risks': risks_found,
                'risk_level': risk_level
            })
        
        return analyzed_clauses





import os
import json
from typing import List, Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re

class FixedLangChainContractAdvisor:
    def __init__(self, model: str = "qwen2.5:3b", base_url: str = "http://192.168.1.4:11434"):
        self.llm = ChatOllama(model=model, base_url=base_url, temperature=0.1)
        self.str_parser = StrOutputParser()
    
    def analyze_clause_with_llm(self, clause_content: str, clause_title: str, risks: List[Dict]) -> Dict[str, Any]:
        """使用修复版的LangChain分析合同条款"""
        try:
            # 构建完整的提示词（不包含变量）
            full_prompt = self._build_complete_prompt(clause_content, clause_title, risks)
            
            # 创建提示词模板（不包含变量）
            prompt = ChatPromptTemplate.from_template("{input}")
            
            # 创建处理链
            chain = prompt | self.llm | self.str_parser
            
            # 执行分析
            response = chain.invoke({"input": full_prompt})
            
            # 解析响应
            return self._parse_llm_response(response)
            
        except Exception as e:
            print(f"LangChain分析失败: {e}")
            return self._fallback_analysis(clause_content, risks)
    
    def _build_complete_prompt(self, clause_content: str, clause_title: str, risks: List[Dict]) -> str:
        """构建完整的提示词（不包含变量）"""
        risk_descriptions = [f"- {risk['description']} ({risk['type']})" for risk in risks]
        risks_text = "\n".join(risk_descriptions) if risk_descriptions else "未发现明显风险"
        
        prompt = f"""你是一个专业的合同审查专家，擅长识别合同风险并提供具体的修改建议。

请严格按照以下JSON格式输出分析结果：
{{
    "risk_analysis": "对条款风险的详细分析",
    "specific_risks": ["具体的风险点1", "风险点2"],
    "modification_suggestions": ["具体的修改建议1", "建议2"],
    "legal_basis": "相关法律依据或商业考量", 
    "negotiation_tips": "谈判建议",
    "risk_level": "低风险|中风险|高风险"
}}

要求：
1. 分析要具体，指出具体哪些词语或句子有问题
2. 修改建议要给出完整的修改后文本
3. 法律依据要引用具体的法律条文或商业实践
4. 用中文回复，保持专业但易懂
5. 风险等级评估要基于风险严重程度

请分析以下合同条款：

【条款标题】{clause_title}

【条款内容】
{clause_content}

【已识别风险】
{risks_text}

请提供专业的合同审查意见：
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 清理响应文本
            cleaned_response = response.strip()
            
            # 尝试提取JSON
            json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                # 进一步清理JSON字符串
                json_str = self._clean_json_string(json_str)
                
                result = json.loads(json_str)
                
                # 验证必需字段
                required_fields = ["risk_analysis", "specific_risks", "modification_suggestions", 
                                 "legal_basis", "negotiation_tips", "risk_level"]
                if all(field in result for field in required_fields):
                    return result
            
            # 如果JSON解析失败，尝试从响应中提取信息
            return self._extract_from_text(cleaned_response)
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"JSON解析错误: {e}")
            return self._extract_from_text(response)
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串"""
        # 移除可能的代码块标记
        json_str = re.sub(r'```json\s*|\s*```', '', json_str)
        json_str = re.sub(r'```\s*|\s*```', '', json_str)
        
        # 修复常见的JSON格式问题
        json_str = re.sub(r',\s*}', '}', json_str)  # 移除尾随逗号
        json_str = re.sub(r',\s*]', ']', json_str)  # 移除数组尾随逗号
        
        return json_str.strip()
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取信息"""
        # 简单的文本分析来提取信息
        risk_analysis = ""
        specific_risks = []
        modification_suggestions = []
        legal_basis = "基于标准合同审查规范"
        negotiation_tips = "建议明确关键商业条款"
        risk_level = "中风险"
        
        # 尝试提取风险分析
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('{') or line.startswith('}'):
                continue
                
            if '风险' in line and len(line) > 10:
                risk_analysis = line
            elif '建议' in line or '修改' in line:
                modification_suggestions.append(line)
            elif '法律' in line or '依据' in line:
                legal_basis = line
            elif '谈判' in line or '协商' in line:
                negotiation_tips = line
            elif '高风险' in line:
                risk_level = "高风险"
            elif '低风险' in line:
                risk_level = "低风险"
        
        # 如果没找到足够的信息，使用回退方案
        if not risk_analysis:
            risk_analysis = text[:300] + "..." if len(text) > 300 else text
        
        if not modification_suggestions:
            modification_suggestions = ["建议由专业法务人员详细审查"]
        
        return {
            "risk_analysis": risk_analysis,
            "specific_risks": specific_risks[:3],
            "modification_suggestions": modification_suggestions[:3],
            "legal_basis": legal_basis,
            "negotiation_tips": negotiation_tips,
            "risk_level": risk_level
        }
    
    def _fallback_analysis(self, clause_content: str, risks: List[Dict]) -> Dict[str, Any]:
        """回退分析方案"""
        risk_types = list(set([risk['type'] for risk in risks]))
        
        return {
            "risk_analysis": f"识别到{len(risks)}个风险点，涉及：{', '.join(risk_types)}",
            "specific_risks": [risk['description'] for risk in risks][:3],
            "modification_suggestions": self._generate_fallback_suggestions(risks),
            "legal_basis": "基于标准合同审查规范",
            "negotiation_tips": "建议明确关键商业条款",
            "risk_level": "高风险" if len(risks) > 3 else "中风险" if risks else "低风险"
        }
    
    def _generate_fallback_suggestions(self, risks: List[Dict]) -> List[str]:
        """生成回退建议"""
        suggestions = []
        
        for risk in risks:
            if any(word in risk['description'] for word in ['付款', '支付', '金额']):
                suggestions.append("建议明确付款时间和条件：'验收合格后15个工作日内支付剩余款项'")
                break
            elif any(word in risk['description'] for word in ['验收', '标准', '交付']):
                suggestions.append("建议具体化验收标准：参照具体的技术规格和验收 checklist")
                break
            elif '违约' in risk['description']:
                suggestions.append("建议明确违约金计算方式和上限")
                break
            elif '管辖' in risk['description']:
                suggestions.append("建议选择中立的管辖法院")
                break
        
        return suggestions if suggestions else ["建议由专业法务人员审查此条款"]




class WorkingContractAI:
    def __init__(self, use_llm: bool = True, model: str = "qwen2.5:3b", base_url: str = "http://192.168.1.4:11434"):
        self.parser = ContractParser()
        self.use_llm = use_llm
        
        if use_llm:
            print(f"🤖 初始化修复版LangChain Ollama模型: {model}")
            self.llm_advisor = FixedLangChainContractAdvisor(model=model, base_url=base_url)
        else:
            self.llm_advisor = None
        
        self.risk_rules = self._load_risk_rules()
    
    def _load_risk_rules(self) -> Dict[str, Any]:
        """加载风险规则"""
        return {
            'financial_risk': {
                'name': '财务风险',
                'keywords': ['支付', '付款', '违约金', '价格', '金额', '赔偿', '利息', '预付款', '尾款'],
                'patterns': [
                    (r'剩余款项.*验收合格后支付', '付款条件模糊'),
                    (r'支付.*总价.*50%', '预付款比例较高'),
                    (r'违约金.*\d+\.?\d*%', '违约金比例需确认')
                ]
            },
            'delivery_risk': {
                'name': '交付风险', 
                'keywords': ['交付', '验收', '标准', '时间', '期限', '延迟', '尽快', '验收标准'],
                'patterns': [
                    (r'按照.*标准验收', '验收标准模糊'),
                    (r'尽快处理', '响应时间不明确'),
                    (r'行业通用标准', '标准定义不清')
                ]
            },
            'legal_risk': {
                'name': '法律风险',
                'keywords': ['争议', '诉讼', '管辖', '知识产权', '保密', '责任', '纠纷'],
                'patterns': [
                    (r'乙方承担全部责任', '责任分配不均'),
                    (r'甲方所在地.*诉讼', '管辖地单方有利'),
                    (r'友好协商解决', '解决方式模糊')
                ]
            }
        }
    
    def analyze_contract(self, file_path: str, use_llm_for_high_risk: bool = True) -> Dict[str, Any]:
        """分析合同"""
        try:
            print("📖 正在解析合同...")
            documents = self.parser.load_contract(file_path)
            clauses = self.parser.split_into_clauses(documents)
            
            print("🔍 正在进行风险分析...")
            analyzed_clauses = []
            
            for i, clause in enumerate(clauses):
                clause_title = clause['metadata']['clause_title']
                print(f"  分析条款 {i+1}/{len(clauses)}: {clause_title}")
                
                # 基础风险分析
                basic_analysis = self._basic_risk_analysis(clause)
                
                # LLM深度分析（只对高风险条款或所有条款）
                if self.use_llm and (not use_llm_for_high_risk or basic_analysis['risk_score'] < 70):
                    print(f"    🤖 使用LLM深度分析: {clause_title}")
                    try:
                        llm_analysis = self.llm_advisor.analyze_clause_with_llm(
                            clause['page_content'],
                            clause_title,
                            basic_analysis['risks']
                        )
                        clause_analysis = {**basic_analysis, **llm_analysis}
                    except Exception as e:
                        print(f"    ⚠️  LLM分析异常，使用基础分析: {e}")
                        clause_analysis = basic_analysis
                else:
                    clause_analysis = basic_analysis
                
                analyzed_clauses.append({
                    **clause,
                    **clause_analysis
                })
            
            # 生成报告
            report = self._generate_report(analyzed_clauses)
            return report
            
        except Exception as e:
            return {'error': f'合同分析失败: {str(e)}'}
    
    def _basic_risk_analysis(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """基础风险分析"""
        content = clause['page_content']
        risks = self._detect_detailed_risks(content)
        risk_score = self._calculate_risk_score(risks)
        
        return {
            'risks': risks,
            'risk_score': risk_score,
            'review_status': '待审核' if risks else '低风险'
        }
    
    def _detect_detailed_risks(self, content: str) -> List[Dict[str, Any]]:
        """检测详细风险"""
        risks = []
        
        for risk_id, rule in self.risk_rules.items():
            for keyword in rule['keywords']:
                if keyword in content:
                    risks.append({
                        'type': rule['name'],
                        'level': 'medium',
                        'description': f'发现关键词: {keyword}',
                        'position': self._find_keyword_position(content, keyword),
                        'category': risk_id
                    })
            
            for pattern, description in rule['patterns']:
                if re.search(pattern, content):
                    risks.append({
                        'type': rule['name'],
                        'level': 'high',
                        'description': description,
                        'position': '条款内容',
                        'category': risk_id
                    })
        
        return risks
    
    def _find_keyword_position(self, content: str, keyword: str) -> str:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if keyword in line:
                return f"第{i+1}行"
        return "条款内容"
    
    def _calculate_risk_score(self, risks: List[Dict[str, Any]]) -> int:
        if not risks:
            return 85
        
        high_risks = len([r for r in risks if r['level'] == 'high'])
        medium_risks = len([r for r in risks if r['level'] == 'medium'])
        
        base_score = 85
        score_reduction = high_risks * 20 + medium_risks * 10
        
        return max(30, base_score - score_reduction)
    
    def _generate_report(self, analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成报告"""
        total_risks = sum(len(clause['risks']) for clause in analysis)
        high_risk_clauses = len([c for c in analysis if c['risk_score'] < 60])
        medium_risk_clauses = len([c for c in analysis if 60 <= c['risk_score'] < 75])
        
        overall_score = sum(c['risk_score'] for c in analysis) // len(analysis)
        
        return {
            'overall_risk_score': overall_score,
            'risk_level': self._get_risk_level(overall_score),
            'total_clauses': len(analysis),
            'total_risks_found': total_risks,
            'high_risk_clauses': high_risk_clauses,
            'medium_risk_clauses': medium_risk_clauses,
            'clauses_analysis': analysis,
            'summary': self._generate_summary(analysis),
            'llm_enhanced': self.use_llm,
            'timestamp': '2024-01-01 10:00:00'
        }
    
    def _get_risk_level(self, score: int) -> str:
        if score >= 80:
            return "低风险"
        elif score >= 60:
            return "中风险"
        else:
            return "高风险"
    
    def _generate_summary(self, analysis: List[Dict[str, Any]]) -> str:
        high_risk_count = len([c for c in analysis if c['risk_score'] < 60])
        
        if high_risk_count == 0:
            return "合同整体风险可控，建议关注个别中风险条款。"
        elif high_risk_count <= 2:
            return "合同存在少量高风险条款，建议重点审查付款条件、违约责任等条款。"
        else:
            return "合同存在多处高风险条款，建议法务部门重点审查。"

# 测试修复版
def test_fixed_contract_ai():
    print("🔧 修复版 ContractAI with LangChain + Ollama")
    print("=" * 70)
    
    try:
        ai = WorkingContractAI(
            use_llm=True,
            model="qwen2.5:3b",
            base_url="http://192.168.1.4:11434"
        )
        
        test_file = "/home/cooper/githubProjects/ContractAI/words/test_contract.docx"
        
        print("开始分析合同...")
        report = ai.analyze_contract(test_file, use_llm_for_high_risk=True)
        
        if 'error' in report:
            print(f"❌ {report['error']}")
            return
        
        # 显示结果
        print(f"\n✅ 审查完成!")
        print(f"📊 整体风险: {report['overall_risk_score']}/100 - {report['risk_level']}")
        print(f"📑 审查条款: {report['total_clauses']} 个")
        print(f"⚠️  风险点: {report['total_risks_found']} 处")
        print(f"🔴 高风险: {report['high_risk_clauses']} 个")
        print(f"🟡 中风险: {report['medium_risk_clauses']} 个")
        
        # 显示LLM分析的详细结果
        print(f"\n🧠 LLM深度分析结果:")
        print("-" * 70)
        
        llm_analyzed_clauses = [c for c in report['clauses_analysis'] if 'risk_analysis' in c and len(c['risk_analysis']) > 50]
        
        for clause in llm_analyzed_clauses[:3]:  # 只显示前3个详细分析
            print(f"\n🔍 {clause['metadata']['clause_title']} (风险等级: {clause.get('risk_level', '未知')})")
            print(f"   📝 分析: {clause['risk_analysis'][:200]}...")
            
            if clause.get('specific_risks'):
                print(f"   ⚠️  具体风险:")
                for risk in clause['specific_risks'][:2]:
                    print(f"      • {risk}")
            
            if clause.get('modification_suggestions'):
                print(f"   💡 修改建议:")
                for suggestion in clause['modification_suggestions'][:2]:
                    print(f"      • {suggestion}")
            
            if clause.get('negotiation_tips'):
                print(f"   💼 谈判建议: {clause['negotiation_tips']}")
        
        print(f"\n📋 共 {len(llm_analyzed_clauses)} 个条款获得LLM深度分析")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_contract_ai()