import json
from datetime import datetime
from typing import List, Dict, Any
import os
from WorkingContractAI import WorkingContractAI
class ContractAISystem:
    """完整的ContractAI系统"""
    
    def __init__(self, model: str = "qwen2.5:3b", base_url: str = "http://192.168.1.4:11434"):
        self.ai = WorkingContractAI(use_llm=True, model=model, base_url=base_url)
        self.analysis_history = []
    
    def analyze_contract_file(self, file_path: str, save_report: bool = True) -> Dict[str, Any]:
        """分析合同文件并生成报告"""
        print(f"📄 开始分析合同: {file_path}")
        
        # 执行分析
        report = self.ai.analyze_contract(file_path)
        
        if 'error' in report:
            print(f"❌ 分析失败: {report['error']}")
            return report
        
        # 添加时间戳
        report['analysis_timestamp'] = datetime.now().isoformat()
        report['file_name'] = os.path.basename(file_path)
        
        # 保存到历史记录
        self.analysis_history.append(report)
        
        # 保存报告
        if save_report:
            self._save_analysis_report(report)
        
        return report
    
    def _save_analysis_report(self, report: Dict[str, Any]):
        """保存分析报告"""
        try:
            # 创建报告目录
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"contract_analysis_{timestamp}.json"
            file_path = os.path.join(reports_dir, file_name)
            
            # 保存JSON报告
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # 生成可读的文本报告
            text_report_path = file_path.replace('.json', '.txt')
            self._generate_text_report(report, text_report_path)
            
            print(f"💾 分析报告已保存:")
            print(f"   JSON: {file_path}")
            print(f"   TEXT: {text_report_path}")
            
        except Exception as e:
            print(f"⚠️  保存报告失败: {e}")
    
    def _generate_text_report(self, report: Dict[str, Any], file_path: str):
        """生成可读的文本报告"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("                ContractAI 智能合同审查报告\n")
            f.write("=" * 80 + "\n\n")
            
            # 基本信息
            f.write("📊 报告摘要\n")
            f.write("-" * 40 + "\n")
            f.write(f"合同文件: {report.get('file_name', '未知')}\n")
            f.write(f"分析时间: {report.get('analysis_timestamp', '未知')}\n")
            f.write(f"整体风险: {report['overall_risk_score']}/100 - {report['risk_level']}\n")
            f.write(f"审查条款: {report['total_clauses']} 个\n")
            f.write(f"发现风险: {report['total_risks_found']} 处\n")
            f.write(f"高风险条款: {report['high_risk_clauses']} 个\n")
            f.write(f"中风险条款: {report['medium_risk_clauses']} 个\n")
            f.write(f"审查摘要: {report['summary']}\n\n")
            
            # 高风险条款详情
            f.write("🔴 高风险条款详情\n")
            f.write("-" * 40 + "\n")
            
            high_risk_clauses = [c for c in report['clauses_analysis'] if c['risk_score'] < 60]
            for clause in high_risk_clauses:
                f.write(f"\n📋 {clause['metadata']['clause_title']}\n")
                f.write(f"风险分数: {clause['risk_score']}/100\n")
                
                if clause.get('risk_analysis'):
                    f.write(f"风险分析: {clause['risk_analysis']}\n")
                
                if clause.get('specific_risks'):
                    f.write("具体风险:\n")
                    for risk in clause['specific_risks']:
                        f.write(f"  • {risk}\n")
                
                if clause.get('modification_suggestions'):
                    f.write("修改建议:\n")
                    for suggestion in clause['modification_suggestions']:
                        f.write(f"  • {suggestion}\n")
                
                if clause.get('negotiation_tips'):
                    f.write(f"谈判建议: {clause['negotiation_tips']}\n")
                
                f.write("-" * 40 + "\n")
            
            # LLM增强分析
            llm_clauses = [c for c in report['clauses_analysis'] if 'risk_analysis' in c and len(c['risk_analysis']) > 50]
            f.write(f"\n🧠 LLM深度分析 ({len(llm_clauses)}个条款)\n")
            f.write("-" * 40 + "\n")
            
            for clause in llm_clauses:
                f.write(f"\n🔍 {clause['metadata']['clause_title']}\n")
                f.write(f"{clause['risk_analysis']}\n")
                
                if clause.get('legal_basis'):
                    f.write(f"法律依据: {clause['legal_basis']}\n")
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """获取分析历史"""
        return self.analysis_history
    
    def generate_comparison_report(self, file_paths: List[str]):
        """生成多合同对比报告"""
        print("📊 开始多合同对比分析...")
        
        comparison_data = []
        for file_path in file_paths:
            print(f"分析: {file_path}")
            report = self.analyze_contract_file(file_path, save_report=False)
            if 'error' not in report:
                comparison_data.append({
                    'file_name': report['file_name'],
                    'risk_score': report['overall_risk_score'],
                    'risk_level': report['risk_level'],
                    'high_risk_clauses': report['high_risk_clauses'],
                    'total_risks': report['total_risks_found']
                })
        
        # 生成对比报告
        self._generate_comparison_text(comparison_data)

# 完整的演示函数
def demo_contract_ai_system():
    """演示完整的ContractAI系统"""
    print("🚀 ContractAI 智能合同审查系统 - 完整演示")
    print("=" * 70)
    
    # 初始化系统
    system = ContractAISystem(model="qwen2.5:3b")
    
    # 分析测试合同
    test_file = "/home/cooper/githubProjects/ContractAI/words/test_contract.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    print("1. 📄 单合同分析演示")
    report = system.analyze_contract_file(test_file)
    
    if 'error' in report:
        print(f"分析失败: {report['error']}")
        return
    
    # 显示关键洞察
    print(f"\n2. 🔍 关键风险洞察")
    print("-" * 50)
    
    high_risk_clauses = [c for c in report['clauses_analysis'] if c['risk_score'] < 60]
    
    for clause in high_risk_clauses[:3]:  # 显示前3个高风险条款
        print(f"\n📍 {clause['metadata']['clause_title']}")
        print(f"   风险分数: {clause['risk_score']}/100")
        
        if clause.get('specific_risks'):
            print(f"   主要风险: {', '.join(clause['specific_risks'][:2])}")
        
        if clause.get('modification_suggestions'):
            best_suggestion = clause['modification_suggestions'][0]
            print(f"   💡 关键建议: {best_suggestion}")
    
    # 显示统计信息
    print(f"\n3. 📈 分析统计")
    print("-" * 50)
    total_clauses = report['total_clauses']
    risky_clauses = len([c for c in report['clauses_analysis'] if c['risk_score'] < 80])
    
    print(f"   审查条款总数: {total_clauses}")
    print(f"   存在风险条款: {risky_clauses} ({risky_clauses/total_clauses*100:.1f}%)")
    print(f"   LLM分析条款: {len([c for c in report['clauses_analysis'] if 'risk_analysis' in c])}")
    print(f"   整体风险等级: {report['risk_level']}")
    
    # 建议下一步行动
    print(f"\n4. 🎯 建议下一步")
    print("-" * 50)
    
    if report['high_risk_clauses'] > 0:
        print("   🔴 建议重点审查高风险条款，特别是:")
        high_risk_titles = [c['metadata']['clause_title'] for c in high_risk_clauses[:2]]
        for title in high_risk_titles:
            print(f"      • {title}")
    else:
        print("   ✅ 合同风险可控，建议关注中风险条款的优化")
    
    print(f"\n💡 提示: 详细报告已保存至 reports/ 目录")

# 交互式分析函数
def interactive_analysis():
    """交互式合同分析"""
    system = ContractAISystem()
    
    while True:
        print("\n" + "="*60)
        print("ContractAI 交互式分析")
        print("="*60)
        print("1. 分析合同文件")
        print("2. 查看分析历史") 
        print("3. 退出")
        
        choice = input("\n请选择操作 (1-3): ").strip()
        
        if choice == '1':
            file_path = input("请输入合同文件路径: ").strip()
            if os.path.exists(file_path):
                system.analyze_contract_file(file_path)
            else:
                print("❌ 文件不存在")
        
        elif choice == '2':
            history = system.get_analysis_history()
            if history:
                print(f"\n📚 分析历史 ({len(history)} 次分析)")
                for i, report in enumerate(history[-5:]):  # 显示最近5次
                    print(f"{i+1}. {report['file_name']} - {report['overall_risk_score']}/100 ({report['risk_level']})")
            else:
                print("暂无分析历史")
        
        elif choice == '3':
            print("👋 感谢使用ContractAI!")
            break
        
        else:
            print("❌ 无效选择")

if __name__ == "__main__":
    # 运行演示
    demo_contract_ai_system()
    
    # 如果想要交互式分析，取消下面的注释
    # interactive_analysis()