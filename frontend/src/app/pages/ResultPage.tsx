import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../components/ui/collapsible";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  PlayCircle,
  Download,
  ChevronDown,
  ChevronRight,
  Check,
} from "lucide-react";

// Mock thumbnail images (using placeholders)
const THUMBNAIL_RECOMMENDATIONS = [
  {
    id: 1,
    time: "07:25",
    reason:
      "인물의 표정이 가장 생생하고, 감정 전달력이 뛰어남. 시청자의 시선을 사로잡는 결정적 순간입니다.",
    priority: 1,
  },
  {
    id: 2,
    time: "03:12",
    reason:
      "화면 구도와 색상 대비가 뛰어나며, 시각적 임팩트가 강함",
    priority: 2,
  },
  {
    id: 3,
    time: "09:48",
    reason:
      "액션 장면으로 시선 집중도가 높고 흥미 유발에 효과적",
    priority: 3,
  },
];

const TITLE_SUGGESTIONS = [
  {
    type: "호기심 유발형",
    text: "이거 안 사면 100% 후회함",
    reason:
      '트렌드 키워드 "후회"를 활용하여 FOMO(Fear of Missing Out) 심리를 자극합니다. 현재 카테고리에서 평균 클릭률 대비 +23% 높은 성과를 보이는 전략입니다.',
    score: 92,
  },
  {
    type: "정보 전달형",
    text: "아이폰 15 프로 솔직 리뷰 (feat. 3개월 사용 후기)",
    reason:
      '"솔직"과 구체적 기간을 명시하여 신뢰도를 높이고, 실사용자 경험을 강조합니다.',
    score: 85,
  },
  {
    type: "부정적 훅",
    text: "절대 사지 마세요 (라고 할 뻔)",
    reason:
      "역설적 표현으로 호기심을 극대화하며, 괄호 활용으로 반전 요소를 암시합니다.",
    score: 88,
  },
];

export default function ResultPage() {
  const navigate = useNavigate();
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [showEmailDialog, setShowEmailDialog] = useState(false);
  const [email, setEmail] = useState("");
  const [thumbnailToggles, setThumbnailToggles] = useState<{
    [key: number]: boolean;
  }>({});
  const [titleToggles, setTitleToggles] = useState<{
    [key: number]: boolean;
  }>({});

  const handleDownloadReport = () => {
    if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      alert(`리포트를 ${email}로 발송했습니다!`);
      setShowEmailDialog(false);
      setEmail("");
    } else {
      alert("유효한 이메일 주소를 입력해주세요.");
    }
  };

  const toggleThumbnailReason = (id: number) => {
    setThumbnailToggles((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const toggleTitleReason = (index: number) => {
    setTitleToggles((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - 4-1 */}
      <header className="bg-white px-8 py-6 border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div
              className="flex items-center gap-2 cursor-pointer"
              onClick={() => navigate("/")}
            >
              <div className="w-10 h-10 bg-[#F04645] rounded-lg flex items-center justify-center">
                <PlayCircle className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-gray-900">
                Hookly
              </span>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => navigate("/upload")}
              >
                다른 영상 분석하기
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowEmailDialog(true)}
              >
                <Download className="w-4 h-4 mr-2" />
                리포트 다운로드
              </Button>
            </div>
          </div>

          {/* File info with thumbnail preview */}
          <div className="flex items-center gap-4">
            <div className="w-32 h-20 bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg flex items-center justify-center">
              <PlayCircle className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold mb-1">
                video_sample.mp4
              </h1>
              <p className="text-sm text-gray-600">
                기술·테크 카테고리
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Left Column - Score & Summary */}
          <div className="space-y-6">
            {/* 4-5 종합 점수 & 해석 */}
            <Card className="col-span-1 p-6 flex flex-col items-center justify-center text-center relative">
              <div className="mb-2">
                <div className="relative inline-block">
                  <div className="w-40 h-40 rounded-full border-8 border-[#F04645] flex items-center justify-center bg-white relative mx-auto">
                    <div className="text-center">
                      <div className="text-5xl font-bold text-[#F04645]">
                        85
                      </div>
                      <div className="text-sm text-gray-600">
                        /100
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <Badge className="bg-green-500 hover:bg-green-600 shadow-sm px-3 py-1 text-sm">
                  Good
                </Badge>
              </div>

              <p className="text-sm text-gray-700 leading-relaxed">
                현재 트렌드와 잘 맞지만,
                <br />
                <strong className="text-[#F04645]">
                  썸네일 채도를 높이면
                </strong>
                <br />더 좋은 성과가 기대됩니다.
              </p>
            </Card>

            {/* 4-2 핵심 요약 카드 */}
            <Card className="p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                💡 이 영상에서 추천하는 전략 요약
              </h2>

              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-sm text-gray-600">
                      썸네일:{" "}
                    </span>
                    <span className="font-semibold">7:25</span>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-sm text-gray-600">
                      제목 전략:{" "}
                    </span>
                    <span className="font-semibold">
                      감정 강조형 제목
                    </span>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-sm text-gray-600">
                      트렌드 일치도:{" "}
                    </span>
                    <span className="font-semibold text-[#F04645]">
                      85점
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Right Column - Thumbnail Recommendations */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              🎯 썸네일 장면 추천
            </h2>

            {/* 4-3 썸네일 장면 추천 with toggles */}
            {THUMBNAIL_RECOMMENDATIONS.map((thumb) => (
              <Card
                key={thumb.id}
                className={`overflow-hidden ${thumb.priority === 1 ? "border-2 border-[#F04645]" : ""}`}
              >
                <div className="aspect-video bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center relative">
                  <PlayCircle className="w-12 h-12 text-white" />
                  <Badge
                    className={`absolute top-3 left-3 ${thumb.priority === 1 ? "bg-[#F04645]" : "bg-gray-700"}`}
                  >
                    {thumb.priority}순위 장면
                  </Badge>
                  <Badge
                    variant="outline"
                    className="absolute top-3 right-3 bg-white"
                  >
                    {thumb.time}
                  </Badge>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="absolute bottom-3 right-3"
                  >
                    <Download className="w-3 h-3 mr-1" />
                    저장
                  </Button>
                </div>

                <Collapsible
                  open={thumbnailToggles[thumb.id]}
                  onOpenChange={() =>
                    toggleThumbnailReason(thumb.id)
                  }
                >
                  <div className="p-4">
                    <CollapsibleTrigger asChild>
                      <Button
                        variant="ghost"
                        className="w-full justify-between p-0 h-auto hover:bg-transparent text-left"
                      >
                        <span className="text-sm font-semibold text-gray-700">
                          추천 이유
                        </span>
                        <ChevronRight
                          className={`w-4 h-4 text-gray-500 transition-transform ${thumbnailToggles[thumb.id] ? "rotate-90" : ""}`}
                        />
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="mt-2">
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {thumb.reason}
                      </p>
                    </CollapsibleContent>
                  </div>
                </Collapsible>
              </Card>
            ))}
          </div>
        </div>

        {/* 4-4 제목 추천 with toggles */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            ✍️ 제목 추천
            <span className="text-sm font-normal text-gray-500">
              - 클릭률 높은 패턴 기준
            </span>
          </h2>

          <div className="space-y-3">
            {TITLE_SUGGESTIONS.map((title, index) => (
              <Card key={index}>
                <Collapsible
                  open={titleToggles[index]}
                  onOpenChange={() => toggleTitleReason(index)}
                >
                  <div className="p-4">
                    <div className="flex items-start gap-3 mb-2">
                      <div className="w-8 h-8 bg-red-50 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="font-bold text-[#F04645]">
                          {index + 1}
                        </span>
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-lg mb-1">
                          "{title.text}"
                        </p>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className="text-xs"
                          >
                            {title.type}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            예상 클릭률: {title.score}점
                          </span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="flex-shrink-0"
                      >
                        복사
                      </Button>
                    </div>

                    <CollapsibleTrigger asChild>
                      <Button
                        variant="ghost"
                        className="w-full justify-start p-0 h-auto hover:bg-transparent text-left mt-2"
                      >
                        <ChevronRight
                          className={`w-4 h-4 text-gray-500 mr-2 transition-transform ${titleToggles[index] ? "rotate-90" : ""}`}
                        />
                        <span className="text-sm text-gray-600">
                          추천 이유 보기
                        </span>
                      </Button>
                    </CollapsibleTrigger>

                    <CollapsibleContent className="mt-3">
                      <div className="pl-6 p-3 bg-gray-50 rounded-lg border-l-4 border-[#F04645]">
                        <p className="text-sm text-gray-700 leading-relaxed">
                          {title.reason}
                        </p>
                      </div>
                    </CollapsibleContent>
                  </div>
                </Collapsible>
              </Card>
            ))}
          </div>
        </div>

        {/* 4-6 근거 및 트렌드 상세 - Collapsible (default collapsed) */}
        <Collapsible
          open={isDetailOpen}
          onOpenChange={setIsDetailOpen}
        >
          <Card className="p-6">
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className="w-full justify-between p-0 h-auto hover:bg-transparent"
              >
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  💡 근거 및 트렌드 상세 분석, 보기
                </h2>
                <ChevronDown
                  className={`w-5 h-5 text-gray-500 transition-transform ${isDetailOpen ? "rotate-180" : ""}`}
                />
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-6">
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <span className="text-[#F04645]">▶</span>내
                    영상 주요 키워드 vs 트렌드 급상승 키워드
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-sm font-semibold text-gray-700 mb-2">
                        내 영상 키워드
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="outline">리뷰</Badge>
                        <Badge variant="outline">아이폰</Badge>
                        <Badge variant="outline">솔직</Badge>
                        <Badge variant="outline">테크</Badge>
                      </div>
                    </div>
                    <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                      <p className="text-sm font-semibold text-gray-700 mb-2">
                        트렌드 급상승 키워드
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <Badge className="bg-[#F04645]">
                          충격
                        </Badge>
                        <Badge className="bg-[#F04645]">
                          결국
                        </Badge>
                        <Badge className="bg-[#F04645]">
                          후회
                        </Badge>
                        <Badge className="bg-[#F04645]">
                          진짜
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <span className="text-[#F04645]">▶</span>
                    시청자 이탈 예상 구간 (30초 훅 진단)
                  </h3>
                  <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <p className="text-sm text-gray-700 leading-relaxed">
                      ⚠️ 영상 시작 <strong>0:00~0:30</strong>{" "}
                      구간의 훅이 다소 약합니다. 더 강렬한
                      오프닝 멘트나 시각적 임팩트를 추가하는
                      것을 권장합니다.
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <span className="text-[#F04645]">▶</span>
                    카테고리 내 경쟁 영상 비교
                  </h3>
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="space-y-2 text-sm text-gray-700">
                      <p>
                        • 상위 10% 영상의 평균 썸네일 밝기:{" "}
                        <strong>72%</strong> (내 영상: 65%)
                      </p>
                      <p>
                        • 평균 제목 길이: <strong>25자</strong>{" "}
                        (권장: 20-30자)
                      </p>
                      <p>
                        • 이모지 사용률: <strong>85%</strong>{" "}
                        (추천: 1-2개 활용)
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* CTA Section */}
        <div className="mt-12 text-center">
          <Button
            size="lg"
            className="bg-[#F04645] hover:bg-[#d93d3c] text-white px-12"
            onClick={() => navigate("/upload")}
          >
            다른 영상 분석하기
          </Button>
        </div>
      </main>

      {/* Email Dialog for Report Download */}
      <Dialog
        open={showEmailDialog}
        onOpenChange={setShowEmailDialog}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>리포트 이메일 발송</DialogTitle>
            <DialogDescription>
              분석 리포트를 받으실 이메일 주소를 입력해주세요.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">이메일 주소</Label>
              <Input
                id="email"
                type="email"
                placeholder="example@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <p className="text-xs text-gray-500">
              * 리포트는 PDF 형식으로 발송되며, 발송까지 최대
              5분이 소요될 수 있습니다.
            </p>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowEmailDialog(false)}
            >
              취소
            </Button>
            <Button
              className="bg-[#F04645] hover:bg-[#d93d3c]"
              onClick={handleDownloadReport}
            >
              <Download className="w-4 h-4 mr-2" />
              발송하기
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}