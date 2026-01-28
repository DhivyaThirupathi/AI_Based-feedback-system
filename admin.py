import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from io import BytesIO
from backend.db import feedbacks, global_issues, db
from backend.auth import authenticate_user, create_user, users_collection

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Admin Dashboard", page_icon="🔒", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {width: 100%;}
    div[data-testid="stExpander"] {border: 1px solid #ddd; border-radius: 5px;}
    .stMetric {background-color: #f0f2f6; padding: 15px; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user_info"] = {}

# =====================================================
# 🔐 LOGIN SCREEN
# =====================================================
if not st.session_state["authenticated"]:
    st.title("🔐 Admin Login Portal")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Please Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                user = authenticate_user(username, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_info"] = user
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password")
    st.stop()

# =====================================================
# 👤 LOGGED IN DASHBOARD
# =====================================================
user = st.session_state["user_info"]
role = user["role"]
access_districts = user["access"]

# --- NEW: Handle Multiple Departments ---
# Data pazhaya format-la string-a irundha list-a maathikkom
raw_category = user.get("role_category", ["All Categories"])
if isinstance(raw_category, str):
    user_depts = [raw_category]
else:
    user_depts = raw_category

# Display String (Eg: "Water, Road")
dept_display = ", ".join(user_depts) if isinstance(user_depts, list) else str(user_depts)

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"👤 **{user['username']}**")
    st.caption(f"Role: {role.upper()}")
    st.caption(f"Depts: {dept_display}") 
    if role == "admin":
        st.caption(f"Access: {', '.join(access_districts)}")
    
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

st.title(f"📊 Dashboard")
st.caption(f"Managed Departments: {dept_display}")

# =====================================================
# 👮 SUPER ADMIN PANEL 
# =====================================================
if role == "super_admin":
    st.markdown("### 👮 Super Admin Controls")
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("➕ Create New Sub-Admin")
            
            new_user = st.text_input("Username", key="new_user_input")
            new_pass = st.text_input("Password", type="password", key="new_pass_input")
            new_email = st.text_input("Email ID", key="new_email_input")
            
            # 1. District Selection
            all_locs = feedbacks.distinct("location.district")
            all_districts = sorted([d for d in all_locs if d])
            selected_access = st.multiselect("Assign Districts", all_districts, key="new_access_input")

            # 2. Role/Department Selection (UPDATED for Multiple & Custom)
            st.write("Assign Departments")
            predefined_categories = ["Water", "Sanitation", "Road", "Electricity", "Health", "Transport", "Safety"]
            
            # Multiselect Box
            selected_categories = st.multiselect(
                "Select Departments", 
                predefined_categories, 
                key="new_role_select"
            )
            
            # Custom Input Box
            custom_dept = st.text_input("➕ Type New Department (Optional)", placeholder="Eg: Drainage, Parks...", key="new_custom_role")
            
            # Combine Both
            final_dept_list = selected_categories.copy()
            if custom_dept:
                final_dept_list.append(custom_dept)
                # Avoid duplicates
                final_dept_list = list(set(final_dept_list))

            if st.button("Create Admin & Send Email", key="create_admin_btn"):
                if new_user and new_pass and selected_access and new_email and final_dept_list:
                    
                    # NOTE: Passing LIST now, not string
                    success, msg = create_user(
                        new_user, new_pass, new_email, 
                        role="admin", 
                        assigned_districts=selected_access,
                        role_category=final_dept_list 
                    )
                    
                    if "Email sent" in msg:
                        st.success(msg)
                    else:
                        st.warning(msg)
                else:
                    st.error("⚠️ Please fill all details (User, Pass, Email, District & Dept).")


        # --- RIGHT SIDE: MANAGE EXISTING ADMINS ---
        with c2:
            st.subheader("📋 Manage Admins")
            
            from backend.auth import update_admin_access, delete_admin
            
            admins = list(users_collection.find({"role": "admin"}))
            
            if not admins:
                st.info("No sub-admins found.")
            else:
                for i, admin in enumerate(admins):
                    u_name = admin['username']
                    
                    # Handle List or String
                    u_role_raw = admin.get('role_category', ['All Categories'])
                    u_role_list = [u_role_raw] if isinstance(u_role_raw, str) else u_role_raw
                    
                    u_access = admin.get('access', [])
                    
                    with st.expander(f"👤 {u_name}"):
                        st.caption(f"Current Depts: {', '.join(u_role_list)}")
                        
                        st.write("#### ✏️ Update Access")
                        
                        # District Update
                        all_locs = feedbacks.distinct("location.district")
                        all_districts = sorted([d for d in all_locs if d])
                        new_districts = st.multiselect(
                            "Update Districts", 
                            options=all_districts, 
                            default=[d for d in u_access if d in all_districts],
                            key=f"dist_{u_name}"
                        )
                        
                        # Dept Update (Multiselect + Custom)
                        predefined_categories = ["Water", "Sanitation", "Road", "Electricity", "Health", "Transport", "Safety"]
                        
                        # Pre-select existing valid ones
                        default_depts = [d for d in u_role_list if d in predefined_categories]
                        
                        updated_categories = st.multiselect(
                            "Update Departments", 
                            options=predefined_categories, 
                            default=default_depts,
                            key=f"role_upd_{u_name}"
                        )
                        
                        updated_custom = st.text_input("Add Custom Dept", key=f"custom_upd_{u_name}")
                        
                        # Merge Logic
                        final_updated_depts = updated_categories.copy()
                        if updated_custom:
                            final_updated_depts.append(updated_custom)
                        
                        # If list is empty, warn or default? Let's keep existing if empty to prevent error
                        if not final_updated_depts:
                            final_updated_depts = u_role_list

                        if st.button("💾 Save Changes", key=f"save_{u_name}"):
                            success, msg = update_admin_access(u_name, new_districts, final_updated_depts)
                            if success:
                                st.success(msg)
                                st.rerun() 
                            else:
                                st.error(msg)
                        
                        st.markdown("---")
                        
                        st.write("#### 🗑️ Delete User")
                        if st.button(f"Delete {u_name}?", key=f"del_{u_name}", type="primary"):
                            success, msg = delete_admin(u_name)
                            if success:
                                st.success(msg)
                                st.rerun() 
                            else:
                                st.error(msg)
st.markdown("---")

# =====================================================
# 🌍 DATA FILTERING LOGIC (UPDATED FOR MULTI-DEPT)
# =====================================================
raw_data = list(feedbacks.find().sort("created_at", -1))

# 1. Filter by District
if role == "super_admin":
    all_data = raw_data
else:
    all_data = [d for d in raw_data if d.get("location", {}).get("district") in access_districts]

# 2. Filter by Department Role (UPDATED)
# Logic: Show data IF "All Categories" is in user's list OR issue category is in user's list
if role != "super_admin":
    # Ensure user_depts is a list
    current_user_depts = user.get("role_category", ["All Categories"])
    if isinstance(current_user_depts, str):
        current_user_depts = [current_user_depts]

    if "All Categories" not in current_user_depts:
        all_data = [d for d in all_data if d.get("ai", {}).get("category") in current_user_depts]

analyzed_feedbacks = [fb for fb in all_data if fb.get("ai")]

total_received = len(all_data)
total_analyzed = len(analyzed_feedbacks)
pending_count = total_received - total_analyzed

# =====================================================
# DASHBOARD UI
# =====================================================

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📢 Total Reports", value=total_received)
with col2:
    st.metric(label="✅ Verified & Processed", value=total_analyzed)
with col3:
    st.metric(label="⏳ Pending", value=pending_count)

st.markdown("---")

# =====================================================
# 🔥 TOP CRITICAL ISSUES (GROUPED)
# =====================================================
st.subheader("🔥 Top Critical Issues (Grouped by Problem)")

if not analyzed_feedbacks:
    st.info("✅ No issues reported yet.")
else:
    grouped_issues = {}

    for fb in analyzed_feedbacks:
        ai_data = fb.get("ai", {})
        loc_data = fb.get("location", {})
        
        issue_name = ai_data.get("main_issue", "Unknown Issue")
        category = ai_data.get("category", "General")
        priority = ai_data.get("priority", "LOW")
        district = loc_data.get("district", "Unknown")
        user_name = fb.get("user", {}).get("name", "Anonymous")

        unique_key = f"{category}_{issue_name}"

        if unique_key in grouped_issues:
            grouped_issues[unique_key]["total_reports"] += 1
            grouped_issues[unique_key]["users"].append(user_name)
            grouped_issues[unique_key]["districts"].add(district)
            
            prio_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            existing_prio_val = prio_map.get(grouped_issues[unique_key]["priority"], 1)
            new_prio_val = prio_map.get(priority, 1)
            
            if new_prio_val > existing_prio_val:
                grouped_issues[unique_key]["priority"] = priority
                
        else:
            grouped_issues[unique_key] = {
                "issue_text": issue_name,
                "category": category,
                "districts": {district},
                "priority": priority,
                "total_reports": 1,
                "users": [user_name]
            }

    final_issue_list = list(grouped_issues.values())
    priority_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    final_issue_list.sort(key=lambda x: (priority_map.get(x["priority"], 1), x["total_reports"]), reverse=True)

    for issue in final_issue_list:
        name = issue["issue_text"]
        count = issue["total_reports"]
        prio = issue["priority"]
        cat = issue["category"]
        
        dist_list = sorted(list(issue["districts"]))
        if len(dist_list) > 3:
            dist_str = ", ".join(dist_list[:3]) + f" (+{len(dist_list)-3} others)"
        else:
            dist_str = ", ".join(dist_list)

        user_list = list(set(issue["users"]))

        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                icon = "🚨" if prio == "CRITICAL" else "🟠" if prio == "HIGH" else "🔵"
                st.markdown(f"### {icon} {name}")
                st.markdown(f"**📍 Locations:** {dist_str} | **📂 Dept:** {cat}")
                
                if len(user_list) > 3:
                    display_users = ", ".join(user_list[:3]) + f" and {len(user_list)-3} others"
                else:
                    display_users = ", ".join(user_list)
                
                st.caption(f"Reported by: {display_users}")
                
            with c2:
                st.metric("Total Reports", count)
                st.caption(f"Status: {prio}")

st.markdown("---")
# =====================================================
# 📊 DISTRICT-WISE FEEDBACK DISTRIBUTION
# =====================================================
st.subheader("📊 Feedback Distribution by Department (District-wise)")
st.caption("Select a district to view department-wise complaint distribution")

if not analyzed_feedbacks:
    st.info("No analyzed feedbacks available for visualization.")
else:
    # Extract available districts from analyzed data
    available_districts = sorted({
        fb.get("location", {}).get("district")
        for fb in analyzed_feedbacks
        if fb.get("location", {}).get("district")
    })

    selected_district = st.selectbox(
        "📍 Select District",
        options=["All Districts"] + available_districts
    )

    # Filter data based on selected district
    if selected_district != "All Districts":
        district_data = [
            fb for fb in analyzed_feedbacks
            if fb.get("location", {}).get("district") == selected_district
        ]
    else:
        district_data = analyzed_feedbacks

    if not district_data:
        st.warning("No feedback data available for this district.")
    else:
        categories = [
            fb.get("ai", {}).get("category", "Other")
            for fb in district_data
        ]

        df_cat = (
            pd.DataFrame(categories, columns=["Department"])
            .value_counts()
            .reset_index(name="Count")
        )

        col_chart, col_table = st.columns([3, 1])

        with col_chart:
            import plotly.express as px

            fig = px.bar(
                df_cat,
                x="Count",
                y="Department",
                orientation="h",
                color="Count",
                color_continuous_scale="Blues",
                text="Count",
            )

            fig.update_layout(
                height=420,
                xaxis_title="Number of Reports",
                yaxis_title="Department",
                margin=dict(l=40, r=20, t=30, b=20),
            )

            fig.update_traces(
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Reports: %{x}<extra></extra>",
            )

            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.markdown("### 📋 Summary")
            st.dataframe(
                df_cat,
                use_container_width=True,
                hide_index=True
            )
# =====================================================
# 📊 DISTRICT & CONSTITUENCY-WISE FEEDBACK DISTRIBUTION
# =====================================================
st.subheader("📊 Feedback Distribution by Department")
st.caption("Select District and Constituency to analyze department-wise complaints")

if not analyzed_feedbacks:
    st.info("No analyzed feedbacks available for visualization.")
else:
    # -------------------------------
    # District Selection
    # -------------------------------
    districts = sorted({
        fb.get("location", {}).get("district")
        for fb in analyzed_feedbacks
        if fb.get("location", {}).get("district")
    })

    selected_district = st.selectbox(
        "📍 Select District",
        options=["Select District"] + districts
    )

    if selected_district == "Select District":
        st.info("Please select a district to continue.")
        st.stop()

    # -------------------------------
    # Constituency Selection
    # -------------------------------
    constituencies = sorted({
        fb.get("location", {}).get("constituency")
        for fb in analyzed_feedbacks
        if fb.get("location", {}).get("district") == selected_district
        and fb.get("location", {}).get("constituency")
    })

    selected_constituency = st.selectbox(
        "🏛️ Select Constituency",
        options=["All Constituencies"] + constituencies
    )

    # -------------------------------
    # Filter Data
    # -------------------------------
    filtered_data = [
        fb for fb in analyzed_feedbacks
        if fb.get("location", {}).get("district") == selected_district
        and (
            selected_constituency == "All Constituencies"
            or fb.get("location", {}).get("constituency") == selected_constituency
        )
    ]

    if not filtered_data:
        st.warning("No feedback data available for this selection.")
    else:
        categories = [
            fb.get("ai", {}).get("category", "Other")
            for fb in filtered_data
        ]

        df_cat = (
            pd.DataFrame(categories, columns=["Department"])
            .value_counts()
            .reset_index(name="Count")
        )

        col_chart, col_table = st.columns([3, 1])

        with col_chart:
            import plotly.express as px

            fig = px.bar(
                df_cat,
                x="Count",
                y="Department",
                orientation="h",
                color="Count",
                color_continuous_scale="Teal",
                text="Count",
            )

            fig.update_layout(
                height=420,
                xaxis_title="Number of Reports",
                yaxis_title="Department",
                margin=dict(l=40, r=20, t=30, b=20),
            )

            fig.update_traces(
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Reports: %{x}<extra></extra>",
            )

            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.markdown("### 📋 Summary")
            st.dataframe(
                df_cat,
                use_container_width=True,
                hide_index=True
            )


if st.checkbox("📂 Click to Show Detailed Data & Download"):
    st.subheader("📋 District-wise Feedback Data")

    if not analyzed_feedbacks:
        st.warning("No verified data available yet.")
    else:
        rows = []
        for fb in analyzed_feedbacks:
            user = fb.get("user", {})
            location = fb.get("location", {})
            ai = fb.get("ai", {})

            rows.append({
                "Name": user.get("name", "N/A"),
                "District": location.get("district", "N/A"),
                "Category": ai.get("category", "N/A"),
                "Priority": ai.get("priority", "N/A"),
                "Issue": ai.get("main_issue", "N/A"),
                "Feedback": fb.get("feedback", {}).get("original_text", ""),
                "Date": fb.get("created_at", "")
            })

        df = pd.DataFrame(rows)

        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            districts = sorted(df["District"].unique().tolist())
            selected_district = st.selectbox("Filter by District:", ["All Districts"] + districts)

        if selected_district != "All Districts":
            filtered_df = df[df["District"] == selected_district]
        else:
            filtered_df = df

        def convert_df_to_excel(dataframe):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                dataframe.to_excel(writer, index=False, sheet_name="Feedbacks")
            return output.getvalue()
        
        excel_data = convert_df_to_excel(filtered_df)

        with col_f2:
            st.write("")
            st.write("")
            st.download_button(
                label="⬇️ Download Excel",
                data=excel_data,
                file_name=f"report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        st.write("### 🗂️ Individual Feedback Analysis")
        for fb in analyzed_feedbacks:
            if selected_district != "All Districts" and fb.get("location", {}).get("district") != selected_district:
                continue
                
            ai = fb.get("ai", {})
            p_emoji = "🔴" if ai.get("priority") == "CRITICAL" else "🟠" if ai.get("priority") == "HIGH" else "🔵"
            
            with st.expander(f"{p_emoji} {fb.get('location', {}).get('district')} - {ai.get('main_issue', 'Issue')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**User:** {fb.get('user', {}).get('name')}")
                    st.info(fb.get("feedback", {}).get("original_text"))
                with c2:
                    st.success(f"**Issue:** {ai.get('main_issue')}")
                    st.write(f"**Summary:** {ai.get('summary')}")