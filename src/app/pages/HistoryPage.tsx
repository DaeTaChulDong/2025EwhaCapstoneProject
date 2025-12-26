import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PlayCircle, Eye, Calendar, TrendingUp } from 'lucide-react';

const HISTORY_DATA = [
  {
    id: 1,
    date: '2025.01.18',
    title: '육아 브이로그',
    category: '브이로그',
    score: 85,
    status: 'Good',
  },
  {
    id: 2,
    date: '2025.01.16',
    title: '주말 일상',
    category: '브이로그',
    score: 72,
    status: 'Average',
  },
  {
    id: 3,
    date: '2025.01.14',
    title: '아이폰 리뷰',
    category: 'IT/테크',
    score: 91,
    status: 'Excellent',
  },
  {
    id: 4,
    date: '2025.01.12',
    title: '요리 레시피',
    category: '요리/먹방',
    score: 78,
    status: 'Good',
  },
];

export default function HistoryPage() {
  const navigate = useNavigate();

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Excellent':
        return <Badge className="bg-green-500">Excellent</Badge>;
      case 'Good':
        return <Badge className="bg-blue-500">Good</Badge>;
      case 'Average':
        return <Badge className="bg-yellow-500">Average</Badge>;
      default:
        return <Badge variant="outline">-</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white px-8 py-6 flex justify-between items-center border-b border-gray-100">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-10 h-10 bg-[#F04645] rounded-lg flex items-center justify-center">
            <PlayCircle className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold text-gray-900">Hookly</span>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate('/upload')}>
            새 분석 시작
          </Button>
          <Button className="bg-[#F04645] hover:bg-[#d93d3c]">
            구독 플랜 관리
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl mb-2">분석 히스토리</h1>
          <p className="text-gray-600">내 분석 기록을 확인하고 다시 볼 수 있습니다</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">총 분석 횟수</p>
                <p className="text-3xl font-bold text-gray-900">4</p>
              </div>
              <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-[#F04645]" />
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">평균 적합도</p>
                <p className="text-3xl font-bold text-gray-900">81.5</p>
              </div>
              <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center">
                <span className="text-2xl">📊</span>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">이번 달 분석</p>
                <p className="text-3xl font-bold text-gray-900">4</p>
              </div>
              <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center">
                <Calendar className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </Card>
        </div>

        {/* History List */}
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">날짜</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">영상 제목</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">카테고리</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">트렌드 적합도</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">상태</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">액션</th>
                </tr>
              </thead>
              <tbody>
                {HISTORY_DATA.map((item) => (
                  <tr key={item.id} className="border-b hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm text-gray-600">{item.date}</td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{item.title}</td>
                    <td className="px-6 py-4">
                      <Badge variant="outline" className="text-xs">
                        {item.category}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-2xl font-bold ${getScoreColor(item.score)}`}>
                        {item.score}
                      </span>
                      <span className="text-sm text-gray-500 ml-1">점</span>
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(item.status)}</td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate('/result')}
                        className="text-[#F04645] hover:text-[#d93d3c] hover:bg-red-50"
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        다시보기
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Subscription CTA */}
        <Card className="mt-8 p-8 bg-gradient-to-br from-white to-red-50 border-2 border-[#F04645]">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold mb-2">무제한 분석을 원하시나요?</h2>
              <p className="text-gray-600">
                프리미엄 플랜으로 업그레이드하고 매월 무제한 분석을 이용하세요
              </p>
              <ul className="mt-4 space-y-2">
                <li className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="text-green-500">✓</span>
                  월 무제한 분석
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="text-green-500">✓</span>
                  우선 처리 (빠른 분석)
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="text-green-500">✓</span>
                  고급 분석 리포트
                </li>
              </ul>
            </div>
            <div className="text-center">
              <div className="mb-4">
                <span className="text-4xl font-bold text-[#F04645]">₩19,900</span>
                <span className="text-gray-600">/월</span>
              </div>
              <Button
                size="lg"
                className="bg-[#F04645] hover:bg-[#d93d3c] text-white"
              >
                프리미엄 시작하기
              </Button>
            </div>
          </div>
        </Card>

        {/* Free Plan Info */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            현재 플랜: <span className="font-semibold">무료 플랜</span> (월 3회 분석 가능)
          </p>
          <p className="text-sm text-gray-500 mt-1">
            남은 분석 횟수: <span className="font-semibold text-[#F04645]">2회</span>
          </p>
        </div>
      </main>
    </div>
  );
}
