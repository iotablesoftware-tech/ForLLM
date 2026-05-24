"use client";

import { useState } from "react";

export interface MenuItemType {
  id: string;
  name: string;
  price: number;
  category: string;
  available: boolean;
}

interface MenuCatalogProps {
  items: MenuItemType[];
  onAddToCart: (item: MenuItemType) => void;
  onZoomImage: (name: string, imgSrc: string) => void;
}

// Category Image Mapper for premium look
const getCategoryIconUrl = (category: string) => {
  const cat = category.toLowerCase();
  if (cat.includes("burger")) return "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=150&q=80";
  if (cat.includes("makarna") || cat.includes("pasta")) return "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=150&q=80";
  if (cat.includes("tatlı") || cat.includes("cheesecake")) return "https://images.unsplash.com/photo-1508737027454-e6454ef45afd?w=150&q=80";
  if (cat.includes("içecek") || cat.includes("limonata") || cat.includes("bira")) return "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=150&q=80";
  return "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=150&q=80";
};

const getMenuItemImageUrl = (category: string) => {
  const cat = category.toLowerCase();
  if (cat.includes("burger")) return "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&q=80";
  if (cat.includes("makarna") || cat.includes("pasta")) return "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&q=80";
  if (cat.includes("tatlı") || cat.includes("cheesecake")) return "https://images.unsplash.com/photo-1508737027454-e6454ef45afd?w=400&q=80";
  if (cat.includes("içecek") || cat.includes("limonata") || cat.includes("bira")) return "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=400&q=80";
  return "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&q=80";
};

export default function MenuCatalog({ items, onAddToCart, onZoomImage }: MenuCatalogProps) {
  const [selectedCategory, setSelectedCategory] = useState("Tümü");

  const uniqueCategories = Array.from(new Set(items.map(item => item.category)));
  const categories = ["Tümü", ...uniqueCategories];

  const filteredItems = selectedCategory === "Tümü"
    ? items
    : items.filter(item => item.category === selectedCategory);

  return (
    <div className="space-y-6 px-4">
      {/* Category Horizontal Selector with Circular Icons (Sleek Mobile Style) */}
      <div className="flex gap-4 overflow-x-auto pb-3 scrollbar-none snap-x snap-mandatory">
        {categories.map((category, idx) => {
          const isActive = selectedCategory === category;
          const iconUrl = category === "Tümü" 
            ? "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=150&q=80" 
            : getCategoryIconUrl(category);

          return (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className="flex flex-col items-center gap-2 shrink-0 snap-center transition-all duration-300 focus:outline-none"
              style={{ animationDelay: `${idx * 30}ms` }}
            >
              {/* Circular Avatar Wrapper */}
              <div 
                className={`h-16 w-16 rounded-full overflow-hidden border-2 transition-all duration-300 shadow-md ${
                  isActive 
                    ? "border-[#c9a84c] scale-105 shadow-[#c9a84c]/20" 
                    : "border-[#2e2e2e] opacity-75 hover:opacity-100"
                }`}
              >
                <img 
                  src={iconUrl} 
                  alt={category} 
                  className="h-full w-full object-cover transition-transform duration-500 hover:scale-110"
                />
              </div>
              <span 
                className={`text-[10px] uppercase font-bold tracking-wider transition-colors ${
                  isActive ? "text-[#c9a84c]" : "text-[#a09070]"
                }`}
              >
                {category}
              </span>
            </button>
          );
        })}
      </div>

      {/* Product Title Section */}
      <div className="flex justify-between items-center border-b border-[#2e2e2e] pb-2">
        <h2 className="font-playfair text-xl font-bold text-[#c9a84c] tracking-wide">
          {selectedCategory === "Tümü" ? "Lezzet Kataloğu" : selectedCategory}
        </h2>
        <span className="text-[10px] font-bold text-[#a09070] bg-[#1a1a1a] border border-[#2e2e2e] px-2 py-0.5 rounded-full">
          {filteredItems.length} Ürün
        </span>
      </div>

      {/* Two Column Grid for Pixel-Perfect Mobile Viewport */}
      <div className="grid grid-cols-2 gap-3.5">
        {filteredItems.map((item, idx) => {
          const imgSrc = getMenuItemImageUrl(item.category);
          return (
            <div
              key={item.id}
              className="group flex flex-col justify-between bg-[#1a1a1a] border border-[#2e2e2e] rounded-xl overflow-hidden hover:border-[#c9a84c]/50 transition-all duration-300 shadow-lg animate-item visible"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              {/* Image zoomable wrapper */}
              <div 
                onClick={() => onZoomImage(item.name, imgSrc)}
                className="relative aspect-square overflow-hidden cursor-zoom-in group-hover:opacity-90 transition-opacity"
              >
                <img 
                  src={imgSrc} 
                  alt={item.name} 
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                  <span className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 text-lg">🔍</span>
                </div>
              </div>

              {/* Product Info */}
              <div className="p-3 flex flex-col justify-between flex-1 gap-2">
                <div className="space-y-1">
                  <h3 className="font-playfair font-bold text-xs text-[#e8e0d0] leading-snug group-hover:text-[#c9a84c] transition-colors line-clamp-2">
                    {item.name}
                  </h3>
                  <span className="text-[10px] font-medium text-[#a09070] uppercase tracking-wide">
                    {item.category}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#2e2e2e]/50">
                  <span className="font-bold text-[#c9a84c] text-xs">₺{item.price}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onAddToCart(item);
                    }}
                    className="px-2 py-1 rounded bg-[#c9a84c]/10 border border-[#c9a84c]/20 hover:bg-[#c9a84c] text-[#c9a84c] hover:text-[#111111] text-[10px] font-bold transition-all duration-300 active:scale-95"
                  >
                    + Ekle
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
