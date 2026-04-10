// src/App.jsx
import React, { useState } from 'react';
import './App.css';
import './Dashboard.css';
import './Upload.css';
import { User } from 'lucide-react';
import logoSvg from './assets/logo.svg'; 

import { DashboardIcon, UploadIcon, SettingsIcon, ArrowIcon, BoltIcon, CopyIcon, DownloadIcon, ChartIcon } from './components/Icons';

function App() {
  const [activeMenu, setActiveMenu] = useState('dashboard');
  const [selectedResult, setSelectedResult] = useState(null);

  const historyData = [
    { id: 1, title: "업로드_한_영상_제목_1.mp4", date: "2026-04-08", progress: 82, isComplete: false, thumbnail: "https://via.placeholder.com/180x100"}, 
    { id: 2, title: "업로드_한_영상_제목_2.mp4", date: "2026-04-07", progress: 100, isComplete: true, thumbnail: "https://via.placeholder.com/180x100"},
  ];

  const menuInfo = {
    dashboard: { title: '내 대시보드', icon: <DashboardIcon /> },
    upload: { title: '영상 업로드', icon: <UploadIcon /> },
    settings: { title: '설정', icon: <SettingsIcon /> },
  };

  return (
    <div className="layout">
      {/* --- 사이드바 --- */}
      <nav className="sidebar">
        <div className="logo-section">
          <img src={logoSvg} alt="Logo" className="img-logo" />
          <div className="wrapper-logotext">
            <h1 className="logo-title">Think:it <span className="pro">Pro</span></h1>
            <div className="creator-workspace">Creator Workspace</div>
          </div>
        </div>

        <ul className="menu">
          {Object.keys(menuInfo).map((key) => (
            <li 
        key={key} 
        className={activeMenu === key ? 'active' : ''} 
        onClick={() => {
          setActiveMenu(key);
          if (key === 'dashboard') {
            setSelectedResult(null);
          }
        }}
      >
              <span className="menu-icon">{menuInfo[key].icon}</span>
              <span>{menuInfo[key].title}</span>
            </li>
          ))}
        </ul>

        <div className="profile-section" onClick={() => setActiveMenu('settings')}>
          <div className="profile-avatar"><User size={24} color="#a0a0a0" /></div>
          <div className="profile-info">
            <div className="profile-name">프로필</div>
            <div className="profile-plan">Pro Plan</div>
          </div>
        </div>
      </nav>

      {/* --- 메인 콘텐츠 --- */}
      <main className="main-content">
        <header className="top-bar">
          <div className="user-info-wrapper">
            <span className="welcome-text">환영합니다, <strong>유저님</strong></span>
            <div className="topbar-profile-img" onClick={() => setActiveMenu('settings')}></div>
          </div>
        </header>
        
        <section className="content">
          <div className="wrapper-pageheader">
            <div className="text-pagetitle">
              <span className="header-icon">{menuInfo[activeMenu].icon}</span>
              <h1 className="h1">{menuInfo[activeMenu].title}</h1>
            </div>
            <div className="divider-accent" />
          </div>

          {/* --- 대시보드 화면 --- */}
          {activeMenu === 'dashboard' && (
            <div className="dashboard-container">
              
              {/* 1. 목록 화면 (selectedResult가 없을 때) */}
              {!selectedResult ? (
                <>
                  <h2 className="history-section-title">분석 히스토리</h2>

                  {historyData.length > 0 ? (
                    <div className="history-list">
                      {historyData.map((item) => (
                        <div key={item.id} className="history-item">
                          <div className="history-thumbnail"><img src={item.thumbnail} alt="thumb" /></div>
                          <div className="history-info">
                            <h3 className="history-video-title">{item.title}</h3>
                            <div className="history-progress-container">
                              <div className="progress-bar-bg"><div className="progress-bar-fill" style={{ width: `${item.progress}%` }}></div></div>
                              <span className="progress-text">{item.progress}% Complete</span>
                            </div>
                            <div className="history-actions">
                              <button 
                                className={`btn-view-result ${item.isComplete ? 'active' : ''}`} 
                                disabled={!item.isComplete}
                                onClick={() => setSelectedResult(item)}
                              >
                                결과 보기
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    
                    <div className="empty-state-container">
                      <h3 className="empty-title">아직 분석한 영상이 없습니다.</h3>
                      <p className="empty-desc">첫 번째 영상을 업로드하고 AI 분석 결과를 확인해 보세요.</p>
                      <button 
                        className="btn-go-upload" 
                        onClick={() => setActiveMenu('upload')} /* 👈 누르면 업로드 메뉴로 이동! */
                      >
                        <span className="btn-icon"><UploadIcon /></span> 영상 업로드하러 가기
                      </button>
                    </div>
                  )}
                </>
              ) : (
                
                
                <div className="result-detail-container">
                  {/* 2. 상세 결과 화면 (selectedResult가 있을 때) */}
                  <div className="result-header">
                    <h2 className="history-section-title">분석 결과</h2>
                    <button className="btn-back" onClick={() => setSelectedResult(null)}>목록으로 돌아가기 &rarr;</button>
                  </div>
                  <h3 className="result-video-title">{selectedResult.title}</h3>

                  <div className="result-top-section">
                    {/* 왼쪽: 트렌드 적합도 */}
                    <div className="result-card score-card">
                      <h4 className="card-title">종합 트렌드 적합도</h4>


                      <div className="score-circle-wrapper">
                        <svg className="progress-svg" viewBox="0 0 192 192">
                      <circle className="progress-bg" cx="96" cy="96" r="86"></circle>
                      <circle className="progress-bar" cx="96" cy="96" r="86"></circle>
                    </svg>
    <div className="score-content">
      <span className="score-number">88<span className="score-max">/ 100</span></span>
    </div>
  </div>


                      <div className="score-label">High Viral Potential</div>
                      <p className="score-desc">썸네일 - 7:15 ~~<br/>제목 - ---<br/>----------</p>
                    </div>

                    {/* 오른쪽: AI 제목 추천 */}
                    <div className="titles-card">
                      <h4 className="card-title">AI 제목 추천</h4>
                      {[1, 2, 3].map((num) => (
                        <div key={num} className="title-recommend-item">
                          <div>
                            <h5 className="recommend-title">추천 {num}</h5>
                            <p className="recommend-desc">Reason: Concrete monetary value combined with authoritative labeling increases CTR by 14% on average.</p>
                          </div>
                          <button className="btn-copy"><CopyIcon /></button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 중간: AI 썸네일 추천 */}
<div className="thumbnails-card">
  <h4 className="card-title">AI 썸네일 추천</h4>
  <div className="thumbnail-grid">
    {['강렬한 클릭 유도형', '감성 스토리형', '깔끔한 정보형'].map((type, idx) => (
      <div key={idx} className="thumb-recommend-item">
        <img src={`https://picsum.photos/seed/${idx+1}/400/225`} alt="" className="recommend-img"/>
        
        {/* 🌟 2. 범인 검거! 아래 태그(thumb-info-content)로 글씨 영역을 꼭 감싸줘야 패딩이 먹힙니다! */}
        <div className="thumb-info-content">
          <div className="thumb-info-row">
            <div className="thumb-text-col"> {/* 👈 요기도 div 대신 클래스 넣어줌 */}
              <h5 className="thumb-type">{type}</h5>
              <p className="thumb-desc">Recommended for mobile feeds</p>
            </div>
            <button className="btn-download"><DownloadIcon /> 다운로드</button>
          </div>
        </div>

      </div>
    ))}
  </div>
</div>

{/* 하단: AI 상세 분석 */}
<div className="result-card analysis-card">
  <h4 className="card-title">AI 상세 분석</h4>
  
  {/* 🌟 3. 범인 검거! bg-chart-icon이 아니라 analysis-icon이어야 CSS의 우측 상단 배치가 먹힙니다! */}
  <div className="analysis-icon">
    <ChartIcon />
  </div>

  <div className="analysis-content"> {/* 🌟 4. 글씨가 아이콘을 안 덮치게 막아주는 방어막 추가! */}
    <p className="analysis-text">
      Our multi-modal engine has analyzed your video sequence and identified a critical drop-off point at 00:42. The visual pacing slows down significantly during the transition, causing a 12% loss in retention compared to top-performing videos in your category. To optimize this, we recommend cutting the 4-second B-roll sequence and replacing it with a high-energy zoom-in on the primary subject.
    </p>
    <p className="analysis-text">
      Furthermore, your lighting profile suggests a high-end editorial feel that perfectly aligns with current luxury-tech trends. We suggest emphasizing this in your color grading by pushing the primary reds slightly further towards the crimson spectrum (#BC0100) to create a stronger brand anchor throughout the series. Your audio levels are balanced, but a 3dB boost in the low-mids for your voice track will increase perceived authority.
    </p>
  </div>
</div>

                  {/* 맨 밑: 공유하기 박스 */}
                  <div className="result-share-box">
                    <div className="share-text-area">
                      <h4>분석 결과 소장 및 공유하기</h4>
                      <p>핵심 인사이트가 담긴 컨설팅 리포트를 이메일로 전송해<br /> 간편하게 저장하고 확인해 보세요.</p>
                    </div>
                    <div className="share-input-area">
                      <input type="email" placeholder="이메일을 입력하세요" className="share-input" />
                      <button className="btn-send-email">리포트 이메일로 받기</button>
                    </div>
                  </div>

                </div>
              )}
            </div>
          )}

          {/* --- 영상 업로드 화면 --- */}
          {activeMenu === 'upload' && (
            <div className="upload-container">
              <div className="upload-left-col">
                <div className="wrapper-uploadinfo">
                  <div className="icon-cloudupload"><UploadIcon /></div>
                  <h2 className="text-guidetitle">동영상 파일을 드래그하거나 클릭해서 업로드하세요</h2>
                  <p className="text-supportinfo">MP4, MOV, WebM 형식 지원 (최대 2GB).</p>
                  <div className="wrapper-actionbuttons">
                    <button className="btn-secondary-local">파일 불러오기</button>
                    <button className="btn-secondary-url">URL 불러오기</button>
                  </div>
                </div>
              </div>
              <div className="upload-right-col">
                <div className="section-analysissettings">
                  <b className="text-sectiontitle">상세 분석 설정</b>
                  <div className="wrapper-formfields">
                    <div className="input-category">
                      <div className="input-label">카테고리 선택</div>
                      <div className="dropdown-wrapper">
                        <select className="dropdown-main"><option>교육</option><option>엔터테인먼트</option></select>
                        <span className="icon-arrow"><ArrowIcon /></span>
                      </div>
                    </div>
                    <div className="input-category">
                      <div className="input-label">AI 맞춤 프롬프트 입력</div>
                      <textarea className="textarea-main" placeholder="예) 배경은 파란색으로 해줘."></textarea>
                      <div className="text-protip-container"><b>Pro Tip: </b><span>디테일하게 요구할수록 분석 퀄리티가 올라갑니다.</span></div>
                    </div>
                  </div>
                </div>
                <button className="btn-start-analysis">AI 분석 시작하기 <span className="icon-bolt"><BoltIcon /></span></button>
              </div>
            </div>
          )}

          {/* --- 설정 화면 --- */}
          {activeMenu === 'settings' && (
            <div className="settings-page">
              <p>계정 및 서비스 설정을 관리합니다.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;