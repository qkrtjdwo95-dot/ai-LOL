import { useEffect, useState, type FormEvent } from 'react'
import { Activity, ArrowRight, ArrowUpRight, BookOpen, ChevronDown, CircleHelp, Clock3, ExternalLink, Gamepad2, History, Search, ShieldCheck, Sparkles, Swords, Trophy, Zap } from 'lucide-react'

type Match = {
  match_id: string; game_mode: string; game_type: string; queue_id: number; game_start: number
  duration: number; champion: string; win: boolean; kills: number; deaths: number; assists: number
  participants: { name: string; tag: string; champion: string; win: boolean }[]
}
type Augment = { id: string; name: string; description: string; tier?: string; category?: string; icon?: string }
type View = 'search' | 'augments'

const REGION_LABEL: Record<string, string> = { kr: '한국', na1: '북미', euw1: '서유럽', eun1: '북유럽', jp1: '일본', br1: '브라질', la1: '라틴 아메리카 북부', la2: '라틴 아메리카 남부', oc1: '오세아니아', tr1: '튀르키예', ru: '러시아', ph2: '필리핀', sg2: '싱가포르', th2: '태국', tw2: '대만', vn2: '베트남' }

export default function App() {
  const [view, setView] = useState<View>('search')
  const [riotId, setRiotId] = useState('')
  const [region, setRegion] = useState('kr')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [matches, setMatches] = useState<Match[]>([])
  const [account, setAccount] = useState<{ game_name: string; tag_line: string } | null>(null)
  const [augments, setAugments] = useState<Augment[]>([])
  const [augmentQuery, setAugmentQuery] = useState('')
  const [augmentTier, setAugmentTier] = useState('')
  const [dbReady, setDbReady] = useState(false)
  const [keyReady, setKeyReady] = useState(false)

  useEffect(() => { fetch('/api/health').then(r => r.json()).then(data => { setDbReady(true); setKeyReady(data.riot_api_key_configured) }).catch(() => setDbReady(false)) }, [])
  useEffect(() => {
    const params = new URLSearchParams()
    if (augmentQuery) params.set('q', augmentQuery)
    if (augmentTier) params.set('tier', augmentTier)
    fetch(`/api/augments?${params}`).then(r => r.json()).then(data => setAugments(data.items ?? [])).catch(() => setAugments([]))
  }, [augmentQuery, augmentTier])

  async function search(event?: FormEvent) {
    event?.preventDefault()
    if (!riotId.includes('#')) { setError('Riot ID를 이름#태그 형식으로 입력해 주세요.'); return }
    setLoading(true); setError(''); setMatches([])
    try {
      const response = await fetch(`/api/summoners/${region}/${encodeURIComponent(riotId.trim())}/matches?count=10`)
      const body = await response.json()
      if (!response.ok) throw new Error(body.detail || '전적을 불러오지 못했습니다.')
      setMatches(body.matches); setAccount(body.account)
    } catch (e) { setError(e instanceof Error ? e.message : '전적을 불러오지 못했습니다.') }
    finally { setLoading(false) }
  }

  const wins = matches.filter(match => match.win).length
  const winRate = matches.length ? Math.round(wins / matches.length * 100) : 0
  const queueName = (match: Match) => match.queue_id === 450 ? '칼바람 나락' : match.game_mode.replaceAll('_', ' ')

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#home" onClick={() => setView('search')}><span className="brand-mark"><Swords size={17} strokeWidth={2.5}/></span><span>LOL<span className="brand-muted">ARCHIVE</span></span></a>
      <div className="side-caption">WORKSPACE</div>
      <button className={`nav-item ${view === 'search' ? 'active' : ''}`} onClick={() => setView('search')}><Activity size={17}/><span>전적 검색</span><span className="nav-shortcut">⌘ 1</span></button>
      <button className={`nav-item ${view === 'augments' ? 'active' : ''}`} onClick={() => setView('augments')}><Sparkles size={17}/><span>아수라장 증강</span><span className="nav-count">NEW</span></button>
      <div className="sidebar-divider" />
      <div className="side-caption">QUICK ACCESS</div>
      <div className="quick-card"><div className="quick-icon"><History size={15}/></div><div><strong>최근 검색</strong><span>전적을 검색하면 보여요</span></div></div>
      <div className="sidebar-bottom">
        <div className="status-row"><span className={`status-dot ${dbReady ? '' : 'dim'}`}/><span>API 서버</span><b>{dbReady ? '연결됨' : '대기 중'}</b></div>
        <div className="status-row"><span className={`status-dot ${keyReady ? '' : 'dim'}`}/><span>Riot API 키</span><b>{keyReady ? '설정됨' : '미설정'}</b></div>
        <div className="profile-chip"><div className="profile-avatar">L</div><div className="profile-label"><strong>소환사 대시보드</strong><span>개인 프로젝트</span></div><CircleHelp size={16}/></div>
      </div>
    </aside>

    <main className="main-content">
      <header className="topbar"><div className="breadcrumb">MY WORKSPACE <span>/</span> <b>{view === 'search' ? '전적 검색' : '아수라장 증강'}</b></div><div className="top-actions"><div className="live-pill"><i/> LIVE DATA</div><button className="icon-button" aria-label="도움말"><CircleHelp size={17}/></button><div className="top-avatar">L</div></div></header>
      {view === 'search' ? <>
        <section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line"/> SUMMONER INTELLIGENCE</div><h1>오늘의 플레이를<br/><span>한눈에 살펴보세요.</span></h1><p className="subtitle">소환사 전적을 검색하고, 아수라장 증강 정보를 확인해 보세요.</p></div><div className="hero-emblem"><div className="emblem-ring ring-a"/><div className="emblem-ring ring-b"/><div className="emblem-core"><Swords size={35}/></div><span className="spark spark-a">✦</span><span className="spark spark-b">✧</span></div></section>
        <form className="search-panel" onSubmit={search}><div className="search-title"><span className="search-icon"><Search size={18}/></span><div><strong>소환사 찾기</strong><span>Riot ID로 최근 게임을 검색해요</span></div></div><div className="search-controls"><label className="region-select"><span>서버</span><select value={region} onChange={e => setRegion(e.target.value)}>{Object.entries(REGION_LABEL).map(([code, name]) => <option key={code} value={code}>{name} ({code.toUpperCase()})</option>)}</select><ChevronDown size={14}/></label><div className="search-input-wrap"><input value={riotId} onChange={e => setRiotId(e.target.value)} placeholder="소환사 이름#태그" aria-label="Riot ID"/><span className="input-hint">예: Hide on bush#KR1</span></div><button className="search-button" type="submit" disabled={loading}>{loading ? <span className="spinner"/> : <>전적 검색 <ArrowRight size={16}/></>}</button></div><div className="search-foot"><span><ShieldCheck size={13}/> Riot ID는 이름#태그 형식으로 입력해 주세요</span><span>최근 10게임 조회</span></div></form>
        {error && <div className="error-banner">{error}</div>}
        {matches.length > 0 ? <section className="results-section"><div className="section-heading"><div><div className="eyebrow">MATCH HISTORY</div><h2>{account?.game_name}<span className="tag">#{account?.tag_line}</span></h2></div><div className="result-stats"><span><Trophy size={15}/> 최근 {matches.length}게임</span><strong>{wins}승 {matches.length-wins}패 <em>{winRate}%</em></strong></div></div><div className="match-list">{matches.map(match => <MatchCard key={match.match_id} match={match} queueName={queueName(match)}/>)}</div></section> : <>
          <div className="section-heading compact"><div><div className="eyebrow">YOUR OVERVIEW</div><h2>게임을 시작할 준비가 됐어요<span className="heading-dot">.</span></h2></div><span className="subtle-label"><Clock3 size={14}/> 실시간 전적 데이터</span></div>
          <div className="overview-grid"><div className="overview-card welcome-card"><div className="card-head"><div className="stat-icon violet"><Gamepad2 size={17}/></div><span>RECENT ACTIVITY</span><ArrowUpRight size={15}/></div><div className="empty-activity"><div className="activity-orbit"><Activity size={22}/></div><strong>아직 조회한 전적이 없어요</strong><span>위에서 Riot ID를 검색하면 최근 경기와<br/>플레이 기록을 이곳에서 볼 수 있어요.</span></div><div className="card-bottom-note"><span className="tiny-dot"/> KR 서버를 포함한 16개 지역 지원</div></div>
            <button className="overview-card augment-teaser" onClick={() => setView('augments')}><div className="card-head"><div className="stat-icon gold"><Sparkles size={17}/></div><span>ARAM MAYHEM</span><ArrowUpRight size={15}/></div><div className="teaser-body"><div><strong>증강 도감</strong><span>아수라장 증강을 찾아보고<br/>효과와 등급을 확인해 보세요.</span></div><div className="rune-art"><Zap size={26}/><span>✦</span></div></div><div className="card-bottom-note"><span className="tiny-dot gold-dot"/> 업데이트되는 증강 데이터베이스</div></button>
            <div className="overview-card winrate-card"><div className="card-head"><div className="stat-icon mint"><Trophy size={17}/></div><span>WIN RATE</span><span className="period">LAST 10</span></div><div className="empty-metric"><span>—<small>%</small></span><p>소환사 검색 후<br/>승률이 표시돼요</p></div><div className="metric-track"><i/></div><div className="metric-footer"><span>0 승</span><span>0 패</span></div></div>
          </div>
          <section className="how-section"><div className="eyebrow">GETTING STARTED</div><h2>시작은 간단해요</h2><div className="steps-row"><div className="step"><span>01</span><div><strong>Riot ID 입력</strong><p>이름과 #태그를 입력해요</p></div></div><ArrowRight className="step-arrow" size={17}/><div className="step"><span>02</span><div><strong>서버 선택</strong><p>계정이 있는 지역을 선택해요</p></div></div><ArrowRight className="step-arrow" size={17}/><div className="step"><span>03</span><div><strong>전적 확인</strong><p>최근 게임 기록을 살펴봐요</p></div></div></div></section>
        </>}
      </> : <>
        <section className="augment-hero"><div className="eyebrow"><span className="eyebrow-line"/> ARAM MAYHEM DATABASE</div><h1>아수라장의 모든<br/><span>증강을 찾아보세요.</span></h1><p className="subtitle">이름이나 효과로 검색해 나에게 맞는 증강을 살펴보세요.</p><div className="augment-search"><Search size={17}/><input value={augmentQuery} onChange={e => setAugmentQuery(e.target.value)} placeholder="증강 이름 또는 효과 검색"/><kbd>⌘ K</kbd></div></section>
        <div className="catalog-toolbar"><div><strong>증강 목록</strong><span className="catalog-count">{augments.length.toString().padStart(2,'0')} ITEMS</span></div><div className="filter-chips">{['전체','실버','골드','프리즘'].map((tier, i) => <button key={tier} className={(augmentTier === (i ? tier : '') ? 'selected ' : '') + (i ? `tier-${i}` : '')} onClick={() => setAugmentTier(i ? tier : '')}>{tier}</button>)}</div></div>
        {augments.length ? <div className="augment-grid">{augments.map((augment, i) => <article className="augment-card" key={augment.id}><div className="augment-card-top"><div className="augment-symbol"><Sparkles size={19}/></div><span className={`tier-badge tier-${augment.tier ?? '기본'}`}>{augment.tier ?? '증강'}</span></div><h3>{augment.name}</h3><p>{augment.description}</p><div className="augment-card-foot"><span>{augment.category ?? 'ARAM MAYHEM'}</span><span>#{String(i+1).padStart(2,'0')}</span></div></article>)}</div> : <div className="catalog-empty"><div className="catalog-empty-icon"><BookOpen size={23}/></div><h3>{augmentQuery || augmentTier ? '조건에 맞는 증강이 없어요' : '증강 데이터를 준비 중이에요'}</h3><p>{augmentQuery || augmentTier ? '검색어를 바꾸거나 필터를 초기화해 보세요.' : <>아수라장 증강은 Riot API에서 직접 제공되지 않아<br/>공식 인게임 데이터를 확인해 카탈로그로 추가해야 해요.</>}</p>{(augmentQuery || augmentTier) && <button onClick={() => { setAugmentQuery(''); setAugmentTier('') }}>필터 초기화 <ArrowRight size={14}/></button>}</div>}
        <div className="data-note"><ShieldCheck size={15}/><span><strong>데이터 출처</strong> 전적은 Riot Games API에서 가져오며, 증강 설명은 Riot 공식 게임 정보를 기반으로 관리합니다.</span><ExternalLink size={13}/></div>
      </>}
      <footer className="footer"><span>LOL ARCHIVE <i>©</i> 2026</span><span>Riot Games와 공식적으로 제휴 또는 승인된 서비스가 아닙니다.</span><a href="https://developer.riotgames.com/policies/general" target="_blank" rel="noreferrer">RIOT API POLICY <ExternalLink size={11}/></a></footer>
    </main>
  </div>
}

function MatchCard({ match, queueName }: { match: Match; queueName: string }) {
  const date = match.game_start ? new Date(match.game_start).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) : '최근'
  const duration = `${Math.floor(match.duration / 60)}:${String(match.duration % 60).padStart(2, '0')}`
  return <article className={`match-card ${match.win ? 'match-win' : 'match-loss'}`}><div className="match-indicator"><span>{match.win ? '승리' : '패배'}</span><small>{queueName}</small></div><div className="champion-portrait">{match.champion.slice(0,1)}</div><div className="match-info"><strong>{match.champion}</strong><span>{date} · {duration} · {match.game_type}</span></div><div className="kda"><strong>{match.kills}<i> / </i><b>{match.deaths}</b><i> / </i>{match.assists}</strong><span>KDA</span></div><div className="match-teammates">{match.participants.slice(0,5).map((p, i) => <span className="mini-champ" title={`${p.name}#${p.tag} · ${p.champion}`} key={`${i}-${p.name}`}>{p.champion.slice(0,1)}</span>)}</div></article>
}
