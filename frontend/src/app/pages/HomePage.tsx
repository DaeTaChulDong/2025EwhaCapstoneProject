import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { PlayCircle } from 'lucide-react';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="px-8 py-6 flex justify-between items-center border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-[#F04645] rounded-lg flex items-center justify-center">
            <PlayCircle className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold text-gray-900">Hookly</span>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate('/upload')}
          className="border-gray-300 text-gray-700 hover:bg-gray-50"
        >
          로그인
        </Button>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex items-center justify-center px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block px-4 py-1 bg-red-50 border border-red-100 rounded-full mb-8">
            <span className="text-[#F04645] text-sm">데이터 기반 유튜브 썸네일 & 제목 AI 컨설턴트</span>
          </div>
          
          <h1 className="text-6xl mb-6 leading-tight">
            <span className="text-gray-900">감으로 만드는</span>
            <br />
            <span className="text-gray-900">썸네일은 </span>
            <span className="text-[#F04645] font-bold">그만.</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-12">
            데이터로 증명된 클릭을 부르세요.
          </p>

          <div className="flex gap-4 justify-center">
            <Button
              size="lg"
              onClick={() => navigate('/upload')}
              className="bg-[#F04645] hover:bg-[#d93d3c] text-white px-8 py-6 text-lg h-auto"
            >
              무료로 시작하기
            </Button>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
            <div className="p-6 bg-white border border-gray-100 rounded-xl text-left hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">AI 장면 추천</h3>
              <p className="text-gray-600 text-sm">영상에서 가장 클릭을 부르는 장면을 AI가 자동으로 찾아드립니다</p>
            </div>

            <div className="p-6 bg-white border border-gray-100 rounded-xl text-left hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">✍️</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">제목 카피라이팅</h3>
              <p className="text-gray-600 text-sm">트렌드 데이터 기반으로 클릭률을 높이는 제목을 생성합니다</p>
            </div>

            <div className="p-6 bg-white border border-gray-100 rounded-xl text-left hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">📊</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">트렌드 분석</h3>
              <p className="text-gray-600 text-sm">카테고리별 실시간 성공 공식을 분석하여 제공합니다</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-8 py-6 border-t border-gray-100 text-center text-sm text-gray-500">
        © 2025 Hookly. All rights reserved.
      </footer>
    </div>
  );
}
