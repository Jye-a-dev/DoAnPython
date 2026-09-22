import { HeroSection } from "@/components/home/hero-section";
import { BentoFeatures } from "@/components/home/bento-features";
import { TechPipeline } from "@/components/home/tech-pipeline";
import { CatalogSection } from "@/components/home/catalog-section";
import { VisualSearchModal } from "@/components/home/visual-search-modal";

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      {/* 1. Hero Section (Split Screen with Scanner Mockup) */}
      <HeroSection />

      {/* 2. Bento Grid Section (4 Blocks Feature Showcase) */}
      <BentoFeatures />

      {/* 3. Tech Architecture Pipeline Section */}
      <TechPipeline />

      {/* 4. Catalog Demo & Smart Filter Section */}
      <CatalogSection />

      {/* 5. Mount VisualSearchModal for AI Camera-to-Shop Flow */}
      <VisualSearchModal />
    </div>
  );
}
