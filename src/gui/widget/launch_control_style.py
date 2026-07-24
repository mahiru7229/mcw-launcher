LAUNCH_CONTROL_STYLE = '''
QLabel#StageBadge {
    background: #344329;
    color: #ffffff;
    border: 2px solid #12140f;
    padding: 4px 8px;
    font-size: 8.5pt;
    font-weight: 900;
}

QLabel#StageBadge[state="busy"] {
    background: #4a3824;
    color: #ffffff;
}

QLabel#StageBadge[state="success"] {
    background: #344329;
    color: #ffffff;
}

QLabel#StageBadge[state="warning"] {
    background: #4a3824;
    color: #ffffff;
}

QLabel#StageBadge[state="error"] {
    background: #5b302f;
    color: #ffffff;
}
'''
