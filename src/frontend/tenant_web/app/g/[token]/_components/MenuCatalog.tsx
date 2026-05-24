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
}

export default function MenuCatalog({ items, onAddToCart }: MenuCatalogProps) {
  const [selectedCategory, setSelectedCategory] = useState("Tümü");

  // Derive categories dynamically from items
  const uniqueCategories = Array.from(new Set(items.map(item => item.category)));
  const categories = ["Tümü", ...uniqueCategories];

  const filteredItems = selectedCategory === "Tümü"
    ? items
    : items.filter(item => item.category === selectedCategory);

  return (
    <div className="space-y-6">
      {/* Category Horizontal Selector */}
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
        {categories.map(category => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded-full text-sm font-semibold transition-all shrink-0 ${
              selectedCategory === category
                ? "bg-primary text-background shadow-md shadow-primary/20"
                : "border border-card-border bg-card-bg text-muted hover:border-primary/30"
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Menu Catalog Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredItems.map(item => (
          <div
            key={item.id}
            className="group rounded-xl border border-card-border bg-card-bg p-5 shadow-sm hover:border-primary/40 transition-all flex flex-col justify-between"
          >
            <div className="space-y-2">
              <div className="flex justify-between items-start">
                <h3 className="font-bold text-lg group-hover:text-primary transition-colors">{item.name}</h3>
                <span className="font-bold text-primary text-base">₺{item.price}</span>
              </div>
            </div>
            
            <div className="pt-4 flex items-center justify-between">
              <span className="text-[10px] uppercase font-semibold tracking-wider text-accent px-2 py-0.5 rounded bg-accent/10">
                Taze Hazırlanır
              </span>
              <button
                onClick={() => onAddToCart(item)}
                className="px-3 py-1.5 rounded-lg bg-primary/10 hover:bg-primary text-primary hover:text-background text-xs font-bold transition-all"
              >
                + Sepete Ekle
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
