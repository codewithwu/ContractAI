# web_interface.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

class ContractAIWebApp:
    def __init__(self):
        self.system = None
        st.set_page_config(
            page_title="ContractAI - 智能合同审查",
            page_icon="📄",
            layout="wide"
        )
    
    def init_system(self):
        """初始化AI系统"""
        if self.system is None:
            from ContractAISystem import ContractAISystem  # 替换为实际模块
            self.system = ContractAISystem()
    
    def run(self):
        """运行Web应用"""
        st.title("📄 ContractAI - 智能合同审查助手")
        st.markdown("---")
        
        # 侧边栏导航
        st.sidebar.title("导航")
        app_mode = st.sidebar.selectbox(
            "选择功能",
            ["合同审查", "分析报告", "风险统计", "使用指南"]
        )
        
        if app_mode == "合同审查":
            self.contract_review_page()
        elif app_mode == "分析报告":
            self.reports_page()
        elif app_mode == "风险统计":
            self.analytics_page()
        else:
            self.guide_page()
    
    def contract_review_page(self):
        """合同审查页面"""
        st.header("📋 合同文件审查")
        
        # 文件上传
        uploaded_file = st.file_uploader(
            "上传合同文件",
            type=['docx', 'pdf'],
            help="支持Word(.docx)和PDF格式"
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if uploaded_file is not None:
                # 保存上传的文件
                file_path = self.save_uploaded_file(uploaded_file)
                
                # 分析选项
                st.subheader("分析设置")
                use_llm = st.checkbox("使用AI深度分析", value=True, help="使用LLM提供专业修改建议")
                analyze_all = st.checkbox("分析所有条款", value=False, help="对所有条款进行AI分析（较慢）")
                
                if st.button("开始分析", type="primary"):
                    with st.spinner("AI正在分析合同中..."):
                        self.init_system()
                        report = self.system.analyze_contract_file(
                            file_path, 
                            save_report=True
                        )
                        
                        if 'error' not in report:
                            self.display_analysis_results(report)
                        else:
                            st.error(f"分析失败: {report['error']}")
        
        with col2:
            st.subheader("💡 使用提示")
            st.info("""
            **最佳实践:**
            - 上传完整的合同文件
            - 启用AI分析获得专业建议  
            - 关注高风险条款的修改建议
            - 保存报告供后续参考
            """)
            
            # 显示最近分析
            if os.path.exists("reports"):
                reports = [f for f in os.listdir("reports") if f.endswith('.json')]
                if reports:
                    st.subheader("最近报告")
                    for report in sorted(reports[-3:], reverse=True):
                        st.caption(f"📄 {report}")
    
    def display_analysis_results(self, report):
        """显示分析结果"""
        st.header("📊 审查结果")
        
        # 风险概览卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "整体风险评分", 
                f"{report['overall_risk_score']}/100",
                delta=f"{report['risk_level']}",
                delta_color="inverse"
            )
        
        with col2:
            st.metric("审查条款", report['total_clauses'])
        
        with col3:
            st.metric("风险点", report['total_risks_found'])
        
        with col4:
            st.metric("高风险条款", report['high_risk_clauses'])
        
        # 风险分布图
        self.display_risk_chart(report)
        
        # 条款详情
        st.subheader("🔍 条款分析详情")
        
        for clause in report['clauses_analysis']:
            self.display_clause_analysis(clause)
    
    def display_risk_chart(self, report):
        """显示风险分布图表"""
        risk_data = {
            '风险等级': ['低风险', '中风险', '高风险'],
            '数量': [
                len([c for c in report['clauses_analysis'] if c['risk_score'] >= 80]),
                len([c for c in report['clauses_analysis'] if 60 <= c['risk_score'] < 80]),
                len([c for c in report['clauses_analysis'] if c['risk_score'] < 60])
            ]
        }
        
        fig = px.pie(
            risk_data, 
            values='数量', 
            names='风险等级',
            color='风险等级',
            color_discrete_map={'高风险':'red', '中风险':'orange', '低风险':'green'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_clause_analysis(self, clause):
        """显示单个条款分析"""
        risk_color = {
            '高风险': '🔴',
            '中风险': '🟡', 
            '低风险': '🟢'
        }.get(clause.get('risk_level', '低风险'), '⚪')
        
        with st.expander(f"{risk_color} {clause['metadata']['clause_title']} - 风险分数: {clause['risk_score']}/100"):
            
            # 条款内容
            st.text_area(
                "条款内容",
                clause['page_content'],
                height=100,
                key=f"content_{clause['metadata']['clause_title']}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 风险分析
                if clause.get('risk_analysis'):
                    st.subheader("📝 风险分析")
                    st.write(clause['risk_analysis'])
                
                # 具体风险
                if clause.get('specific_risks'):
                    st.subheader("⚠️ 具体风险")
                    for risk in clause['specific_risks']:
                        st.write(f"• {risk}")
            
            with col2:
                # 修改建议
                if clause.get('modification_suggestions'):
                    st.subheader("💡 修改建议")
                    for suggestion in clause['modification_suggestions']:
                        st.write(f"• {suggestion}")
                
                # 法律依据和谈判建议
                if clause.get('legal_basis'):
                    st.subheader("⚖️ 法律依据")
                    st.write(clause['legal_basis'])
                
                if clause.get('negotiation_tips'):
                    st.subheader("💼 谈判建议")
                    st.write(clause['negotiation_tips'])
    
    def reports_page(self):
        """分析报告页面"""
        st.header("📚 历史分析报告")
        
        if not os.path.exists("reports"):
            st.info("暂无分析报告")
            return
        
        reports = [f for f in os.listdir("reports") if f.endswith('.json')]
        
        if not reports:
            st.info("暂无分析报告")
            return
        
        # 报告列表
        selected_report = st.selectbox(
            "选择报告",
            sorted(reports, reverse=True),
            format_func=lambda x: f"{x.replace('contract_analysis_', '').replace('.json', '')}"
        )
        
        if selected_report:
            report_path = os.path.join("reports", selected_report)
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            self.display_report_summary(report)
    
    def analytics_page(self):
        """风险统计页面"""
        st.header("📈 风险分析统计")
        
        if not os.path.exists("reports"):
            st.info("暂无分析数据")
            return
        
        # 收集所有报告数据
        all_reports = []
        for report_file in os.listdir("reports"):
            if report_file.endswith('.json'):
                with open(os.path.join("reports", report_file), 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    all_reports.append(report)
        
        if not all_reports:
            st.info("暂无分析数据")
            return
        
        # 风险趋势图
        df = pd.DataFrame([
            {
                '文件': report['file_name'],
                '风险分数': report['overall_risk_score'],
                '高风险条款': report['high_risk_clauses'],
                '分析时间': report.get('analysis_timestamp', '')
            }
            for report in all_reports
        ])
        
        if not df.empty:
            fig = px.line(
                df, 
                x='文件', 
                y='风险分数',
                title='合同风险趋势',
                markers=True
            )
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
            
            # 风险类型分布
            risk_types = {}
            for report in all_reports:
                for clause in report['clauses_analysis']:
                    for risk in clause.get('risks', []):
                        risk_type = risk['type']
                        risk_types[risk_type] = risk_types.get(risk_type, 0) + 1
            
            if risk_types:
                fig2 = px.bar(
                    x=list(risk_types.keys()),
                    y=list(risk_types.values()),
                    title="风险类型分布"
                )
                st.plotly_chart(fig2, use_container_width=True)
    
    def guide_page(self):
        """使用指南页面"""
        st.header("📖 使用指南")
        
        st.subheader("🎯 产品定位")
        st.write("""
        ContractAI是一款面向企业业务部门的智能合同审查助手，致力于在业务签署前提供即时、精准的
        财务与操作性风险识别，并直接给出具备法律/商业依据的修改方案。
        """)
        
        st.subheader("🛠️ 核心功能")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("""
            **🔍 智能风险识别**
            - 财务条款风险
            - 操作性风险  
            - 法律合规风险
            - 模糊条款识别
            """)
            
            st.write("""
            **📝 专业修改建议**
            - 具体修改文本
            - 法律依据说明
            - 商业考量分析
            - 谈判策略建议
            """)
        
        with col2:
            st.write("""
            **📊 风险评估**
            - 整体风险评分
            - 条款级风险分析
            - 风险等级分类
            - 趋势统计分析
            """)
            
            st.write("""
            **💾 报告管理**
            - 自动报告生成
            - 历史记录保存
            - 多格式导出
            - 对比分析
            """)
        
        st.subheader("🚀 快速开始")
        st.write("""
        1. **上传合同**: 在"合同审查"页面上传Word或PDF格式的合同文件
        2. **设置分析**: 选择是否使用AI深度分析（推荐开启）
        3. **查看结果**: 系统将自动分析并生成详细报告
        4. **采取行动**: 根据建议修改合同或进行谈判
        """)
    
    def save_uploaded_file(self, uploaded_file):
        """保存上传的文件"""
        uploads_dir = "uploads"
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        file_path = os.path.join(uploads_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path

# 运行应用
if __name__ == "__main__":
    app = ContractAIWebApp()
    app.run()