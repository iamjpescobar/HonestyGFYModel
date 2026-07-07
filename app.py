if st.session_state.selected_batter:
    sb = st.session_state.selected_batter
    if sb in df_lineup.index:
        stats = df_lineup.loc[sb]
        st.markdown(f"#### 📊 Detailed Scout Matrix: {sb}")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div style="background-color: {get_status_color(stats["💥 SLAM Index"], 65.0)}; padding: 10px; border-radius: 5px; border: 1px solid #333; color: white;"><strong>SLAM: {stats["💥 SLAM Index"]}</strong></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div style="background-color: {get_status_color(stats["Brl %"], 10.0)}; padding: 10px; border-radius: 5px; border: 1px solid #333; color: white;"><strong>Barrel: {stats["Brl %"]}%</strong></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="background-color: {get_status_color(stats["HH %"], 40.0)}; padding: 10px; border-radius: 5px; border: 1px solid #333; color: white;"><strong>HardHit: {stats["HH %"]}%</strong></div>', unsafe_allow_html=True)
        with c4:
            st.container(border=True).metric("Total BBE", f"{stats['BBE']}")
        
        st.markdown("#### 🎯 Arsenal Compatibility Matrix")
        pitcher_arsenal = ['4-Seam Fastball', 'Slider', 'Changeup', 'Sinker']
        comp_data = get_pitch_success_rate(sb, pitcher_arsenal)
        comp_df = pd.DataFrame.from_dict(comp_data, orient='index', columns=['Success Multiplier'])
        st.bar_chart(comp_df)
        
        st.markdown("#### 📋 Detailed Data")
        styled_df = df_lineup.style.format({
            "BBE": "{:d}", "💥 SLAM Index": "{:.1f}", "Brl %": "{:.1f}%",
            "PullAir %": "{:.1f}%", "HH %": "{:.1f}%", "LD %": "{:.1f}%", "GB %": "{:.1f}%"
        }).apply(highlight_slam, axis=1)
        st.dataframe(styled_df, use_container_width=True)
