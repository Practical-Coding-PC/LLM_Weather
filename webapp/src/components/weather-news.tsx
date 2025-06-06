import { ExternalLink } from "lucide-react";
import {
  Drawer,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "./ui/drawer";

type WeatherNewsProps = {
  newsTitle: string;
  summary: string;
  linkUrl: string;
};

export function WeatherNews({ newsTitle, summary, linkUrl }: WeatherNewsProps) {
  return (
    <Drawer>
      <DrawerTrigger asChild>
        <div className="bg-white/40 backdrop-blur border border-gray-200 rounded-lg p-4 flex-grow mb-4 cursor-pointer hover:bg-white/70 transition-colors">
          <h3 className="font-semibold text-gray-800">{newsTitle}</h3>
        </div>
      </DrawerTrigger>

      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>{newsTitle}</DrawerTitle>
        </DrawerHeader>

        <div className="px-4 space-y-4">
          <div>
            <h4 className="font-medium text-gray-800 mb-2">요약</h4>
            <p className="text-sm text-gray-700 leading-relaxed">{summary}</p>
          </div>
        </div>
        <DrawerFooter>
          {linkUrl && (
            <div className="pt-4 border-t border-gray-200 text-right">
              <a
                href={linkUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium"
                onClick={(e) => e.stopPropagation()}
              >
                <span className="mr-2">원본 기사 읽기</span>
                <ExternalLink size={16} />
              </a>
            </div>
          )}
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
}
