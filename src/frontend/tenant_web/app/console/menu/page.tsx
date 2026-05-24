"use client";

import { useState, useEffect, useTransition } from "react";
import Link from "next/link";
import {
  getCategoriesAction,
  getMenuItemsAction,
  createCategoryAction,
  updateCategoryAction,
  deleteCategoryAction,
  createMenuItemAction,
  updateMenuItemAction,
  deleteMenuItemAction,
  Category,
  MenuItem,
} from "../_api/menuActions";

export default function MenuCatalogConsole() {
  // Loading & State variables
  const [categories, setCategories] = useState<Category[]>([]);
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [isPending, startTransition] = useTransition();

  // Dialog/Modal State variables
  const [categoryModal, setCategoryModal] = useState<{
    open: boolean;
    mode: "create" | "edit";
    id?: string;
    name: string;
    displayOrder: number;
  }>({ open: false, mode: "create", name: "", displayOrder: 0 });

  const [itemModal, setItemModal] = useState<{
    open: boolean;
    mode: "create" | "edit";
    id?: string;
    name: string;
    price: number;
    stationCode: string;
    status: string;
  }>({ open: false, mode: "create", name: "", price: 0, stationCode: "kitchen_main", status: "active" });

  // Load initial data
  const loadCatalogData = async () => {
    try {
      setLoading(true);
      const cats = await getCategoriesAction();
      const items = await getMenuItemsAction();
      
      setCategories(cats);
      setMenuItems(items);
      
      if (cats.length > 0 && !selectedCategoryId) {
        setSelectedCategoryId(cats[0].id);
      }
      setLoading(false);
    } catch (err: any) {
      showToast("error", err.message || "Katalog verileri yüklenirken hata oluştu.");
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCatalogData();
  }, []);

  const showToast = (type: "success" | "error", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  // --- CATEGORY OPERATIONS ---

  const handleCategorySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryModal.name.trim()) return;

    startTransition(async () => {
      try {
        if (categoryModal.mode === "create") {
          const created = await createCategoryAction(categoryModal.name, categoryModal.displayOrder);
          setCategories(prev => [...prev, created].sort((a, b) => a.display_order - b.display_order));
          setSelectedCategoryId(created.id);
          showToast("success", `Kategori '${created.name}' başarıyla eklendi.`);
        } else if (categoryModal.mode === "edit" && categoryModal.id) {
          const updated = await updateCategoryAction(categoryModal.id, categoryModal.name, categoryModal.displayOrder);
          setCategories(prev => prev.map(c => c.id === updated.id ? updated : c).sort((a, b) => a.display_order - b.display_order));
          showToast("success", `Kategori '${updated.name}' başarıyla güncellendi.`);
        }
        setCategoryModal({ open: false, mode: "create", name: "", displayOrder: 0 });
      } catch (err: any) {
        showToast("error", err.message || "Kategori kaydedilirken hata oluştu.");
      }
    });
  };

  const handleCategoryDelete = async (id: string, name: string) => {
    if (!confirm(`'${name}' kategorisini silmek istediğinize emin misiniz?`)) return;

    startTransition(async () => {
      try {
        await deleteCategoryAction(id);
        setCategories(prev => prev.filter(c => c.id !== id));
        if (selectedCategoryId === id) {
          const remaining = categories.filter(c => c.id !== id);
          setSelectedCategoryId(remaining.length > 0 ? remaining[0].id : null);
        }
        showToast("success", `Kategori '${name}' başarıyla silindi.`);
      } catch (err: any) {
        showToast("error", err.message || "Kategori silinemedi.");
      }
    });
  };

  // --- MENU ITEM OPERATIONS ---

  const handleItemSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCategoryId || !itemModal.name.trim() || itemModal.price <= 0) return;

    startTransition(async () => {
      try {
        if (itemModal.mode === "create") {
          const created = await createMenuItemAction(
            itemModal.name,
            itemModal.price,
            selectedCategoryId,
            itemModal.stationCode
          );
          setMenuItems(prev => [...prev, created].sort((a, b) => a.name.localeCompare(b.name)));
          showToast("success", `Ürün '${created.name}' başarıyla oluşturuldu.`);
        } else if (itemModal.mode === "edit" && itemModal.id) {
          const updated = await updateMenuItemAction(
            itemModal.id,
            itemModal.name,
            itemModal.price,
            selectedCategoryId,
            itemModal.stationCode,
            itemModal.status
          );
          setMenuItems(prev => prev.map(i => i.id === updated.id ? updated : i).sort((a, b) => a.name.localeCompare(b.name)));
          showToast("success", `Ürün '${updated.name}' başarıyla güncellendi.`);
        }
        setItemModal({ open: false, mode: "create", name: "", price: 0, stationCode: "kitchen_main", status: "active" });
      } catch (err: any) {
        showToast("error", err.message || "Ürün kaydedilirken hata oluştu.");
      }
    });
  };

  const handleItemDelete = async (id: string, name: string) => {
    if (!confirm(`'${name}' ürününü silmek istediğinize emin misiniz?`)) return;

    startTransition(async () => {
      try {
        await deleteMenuItemAction(id);
        setMenuItems(prev => prev.filter(i => i.id !== id));
        showToast("success", `Ürün '${name}' başarıyla silindi.`);
      } catch (err: any) {
        showToast("error", err.message || "Ürün silinemedi.");
      }
    });
  };

  // Filter products by selected category
  const activeCategory = categories.find(c => c.id === selectedCategoryId);
  const filteredItems = menuItems.filter(item => item.category_id === selectedCategoryId);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <span className="h-10 w-10 rounded-full border-4 border-accent border-t-transparent animate-spin" />
        <p className="text-muted text-sm font-semibold tracking-wider uppercase">Menü Kataloğu Yükleniyor...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 flex flex-col flex-1 relative select-none">
      {/* Header and Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-card-border">
        <div>
          <div className="flex items-center gap-2 text-xs text-muted mb-1">
            <Link href="/console" className="hover:text-foreground transition-colors">Konsol</Link>
            <span>/</span>
            <span className="text-accent font-semibold">Menü & Ürün Yönetimi</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Dinamik Menü Kataloğu</h1>
          <p className="text-muted text-sm mt-1">
            Kategorileri düzenleyin, yeni ürünler ekleyin, istasyonları ve fiyatlandırmaları yönetin.
          </p>
        </div>

        <div className="flex gap-2.5">
          <button
            onClick={() => setCategoryModal({ open: true, mode: "create", name: "", displayOrder: categories.length + 1 })}
            className="h-10 px-4 rounded-xl border border-card-border bg-card-bg text-xs font-bold text-foreground hover:bg-[#222222] transition-colors"
          >
            + Yeni Kategori
          </button>
          {selectedCategoryId && (
            <button
              onClick={() => setItemModal({ open: true, mode: "create", name: "", price: 0, stationCode: "kitchen_main", status: "active" })}
              className="h-10 px-4 rounded-xl bg-accent text-background text-xs font-bold hover:bg-accent-hover transition-colors"
            >
              + Kategoriye Ürün Ekle
            </button>
          )}
        </div>
      </div>

      {/* Floating Notification Toast */}
      {notification && (
        <div 
          className={`fixed bottom-6 right-6 z-[300] max-w-sm rounded-xl px-4 py-3 shadow-2xl flex items-center gap-3 animate-bounce border ${
            notification.type === "success" 
              ? "bg-[#162a1c] border-[#22c55e]/30 text-[#22c55e]" 
              : "bg-[#2a1616] border-[#ef4444]/30 text-[#ef4444]"
          }`}
        >
          <span className="text-base">{notification.type === "success" ? "✓" : "⚠"}</span>
          <p className="text-xs font-bold">{notification.message}</p>
        </div>
      )}

      {/* Main Grid layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column: Categories List */}
        <div className="lg:col-span-1 bg-card-bg border border-card-border rounded-2xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-card-border bg-[#151515] flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-accent">Menü Kategorileri</h2>
            <span className="text-[10px] font-bold text-muted bg-[#222222] px-2 py-0.5 rounded-full">{categories.length} Adet</span>
          </div>

          <div className="divide-y divide-card-border">
            {categories.length > 0 ? (
              categories.map((cat) => {
                const isActive = selectedCategoryId === cat.id;
                const catItemCount = menuItems.filter(i => i.category_id === cat.id).length;

                return (
                  <div
                    key={cat.id}
                    onClick={() => setSelectedCategoryId(cat.id)}
                    className={`p-4 flex items-center justify-between cursor-pointer transition-colors ${
                      isActive ? "bg-accent/5 border-l-2 border-accent" : "hover:bg-[#1a1a1a]"
                    }`}
                  >
                    <div className="space-y-0.5">
                      <span className={`text-xs font-bold tracking-wide transition-colors ${isActive ? "text-accent" : "text-foreground"}`}>
                        {cat.name}
                      </span>
                      <div className="flex items-center gap-2 text-[10px] text-muted">
                        <span>Sıra: {cat.display_order}</span>
                        <span>•</span>
                        <span>{catItemCount} ürün</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => setCategoryModal({ open: true, mode: "edit", id: cat.id, name: cat.name, displayOrder: cat.display_order })}
                        className="h-7 w-7 rounded bg-[#222222] text-xs text-muted hover:text-accent hover:bg-[#2c2c2c] flex items-center justify-center transition-colors"
                        title="Düzenle"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleCategoryDelete(cat.id, cat.name)}
                        className="h-7 w-7 rounded bg-[#222222] text-xs text-muted hover:text-error hover:bg-error/10 flex items-center justify-center transition-colors"
                        title="Sil"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-8 text-center text-muted text-xs">
                Kayıtlı kategori bulunamadı. Lütfen yeni bir kategori ekleyin.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Menu Items inside Selected Category */}
        <div className="lg:col-span-2 bg-card-bg border border-card-border rounded-2xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-card-border bg-[#151515] flex justify-between items-center">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-accent">
                {activeCategory ? `'${activeCategory.name}' Ürünleri` : "Menü Ürünleri"}
              </h2>
            </div>
            <span className="text-[10px] font-bold text-muted bg-[#222222] px-2 py-0.5 rounded-full">{filteredItems.length} Ürün</span>
          </div>

          <div className="divide-y divide-card-border">
            {filteredItems.length > 0 ? (
              filteredItems.map((item) => (
                <div key={item.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-[#1a1a1a] transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold tracking-wide text-foreground">{item.name}</span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        item.status === "active" ? "bg-success/10 text-success" :
                        item.status === "out_of_stock" ? "bg-warning/10 text-warning" :
                        "bg-[#2e2e2e] text-muted"
                      }`}>
                        {item.status === "active" ? "Aktif" : item.status === "out_of_stock" ? "Tükendi" : "Pasif"}
                      </span>
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-3 text-[10px] text-muted font-medium">
                      <span className="bg-[#222222] px-2 py-0.5 rounded text-accent font-semibold">₺{item.price}</span>
                      <span>•</span>
                      <span>İstasyon: <strong className="font-mono text-[#a09070]">{item.station_code === "kitchen_main" ? "Ana Mutfak" : "Bar/İçecekler"}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => setItemModal({
                        open: true,
                        mode: "edit",
                        id: item.id,
                        name: item.name,
                        price: item.price,
                        stationCode: item.station_code,
                        status: item.status
                      })}
                      className="h-8 px-3 rounded-lg bg-[#222222] text-xs font-semibold text-muted hover:text-accent hover:bg-[#2c2c2c] flex items-center gap-1.5 transition-colors"
                    >
                      ✏️ Düzenle
                    </button>
                    <button
                      onClick={() => handleItemDelete(item.id, item.name)}
                      className="h-8 w-8 rounded-lg bg-[#222222] text-xs text-muted hover:text-error hover:bg-error/10 flex items-center justify-center transition-colors"
                      title="Sil"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-12 text-center text-muted text-xs flex flex-col items-center justify-center space-y-3">
                <span className="text-xl">🍔</span>
                <p>Bu kategoriye ait herhangi bir ürün bulunmamaktadır.</p>
                {selectedCategoryId && (
                  <button
                    onClick={() => setItemModal({ open: true, mode: "create", name: "", price: 0, stationCode: "kitchen_main", status: "active" })}
                    className="px-3 py-1.5 rounded-lg border border-accent/20 bg-accent/5 text-accent text-[11px] font-bold hover:bg-accent hover:text-background transition-colors"
                  >
                    + İlk Ürünü Ekle
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ─── MODAL DIALOG: CATEGORY CREATE/EDIT ─── */}
      {categoryModal.open && (
        <div className="fixed inset-0 z-[250] bg-black/70 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#1a1a1a] border border-card-border rounded-2xl shadow-2xl overflow-hidden animate-item visible">
            <div className="p-4 border-b border-card-border bg-[#151515] flex justify-between items-center">
              <h3 className="text-xs font-bold uppercase tracking-wider text-accent">
                {categoryModal.mode === "create" ? "Yeni Menü Kategorisi Ekle" : "Kategoriyi Düzenle"}
              </h3>
              <button 
                onClick={() => setCategoryModal({ open: false, mode: "create", name: "", displayOrder: 0 })}
                className="text-muted hover:text-foreground text-xs"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCategorySubmit} className="p-5 space-y-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-muted tracking-wider">Kategori Adı</label>
                <input
                  type="text"
                  required
                  placeholder="Ör. Burgerler, Tatlılar..."
                  value={categoryModal.name}
                  onChange={(e) => setCategoryModal(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-muted tracking-wider">Görüntüleme Sırası</label>
                <input
                  type="number"
                  required
                  min="0"
                  placeholder="Ör. 1, 2, 3..."
                  value={categoryModal.displayOrder}
                  onChange={(e) => setCategoryModal(prev => ({ ...prev, displayOrder: parseInt(e.target.value) || 0 }))}
                  className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setCategoryModal({ open: false, mode: "create", name: "", displayOrder: 0 })}
                  className="h-9 px-4 rounded-lg border border-card-border text-xs font-semibold text-muted hover:bg-[#222222] transition-colors"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={isPending}
                  className="h-9 px-4 rounded-lg bg-accent text-background text-xs font-bold hover:bg-accent-hover disabled:opacity-50 transition-colors"
                >
                  {isPending ? "Kaydediliyor..." : "Kaydet"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL DIALOG: MENU ITEM CREATE/EDIT ─── */}
      {itemModal.open && (
        <div className="fixed inset-0 z-[250] bg-black/70 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#1a1a1a] border border-card-border rounded-2xl shadow-2xl overflow-hidden animate-item visible">
            <div className="p-4 border-b border-card-border bg-[#151515] flex justify-between items-center">
              <h3 className="text-xs font-bold uppercase tracking-wider text-accent">
                {itemModal.mode === "create" ? "Yeni Menü Ürünü Ekle" : "Ürünü Düzenle"}
              </h3>
              <button 
                onClick={() => setItemModal({ open: false, mode: "create", name: "", price: 0, stationCode: "kitchen_main", status: "active" })}
                className="text-muted hover:text-foreground text-xs"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleItemSubmit} className="p-5 space-y-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-muted tracking-wider">Ürün Adı</label>
                <input
                  type="text"
                  required
                  placeholder="Ör. Moda Special Burger"
                  value={itemModal.name}
                  onChange={(e) => setItemModal(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-muted tracking-wider">Fiyat (TRY)</label>
                  <input
                    type="number"
                    required
                    step="0.01"
                    min="0.01"
                    placeholder="250.00"
                    value={itemModal.price || ""}
                    onChange={(e) => setItemModal(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
                    className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-muted tracking-wider">Hazırlık İstasyonu</label>
                  <select
                    value={itemModal.stationCode}
                    onChange={(e) => setItemModal(prev => ({ ...prev, stationCode: e.target.value }))}
                    className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="kitchen_main">Ana Mutfak</option>
                    <option value="bar_beverages">Bar / İçecekler</option>
                  </select>
                </div>
              </div>

              {itemModal.mode === "edit" && (
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-muted tracking-wider">Durum</label>
                  <select
                    value={itemModal.status}
                    onChange={(e) => setItemModal(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="active">Aktif (Satışta)</option>
                    <option value="out_of_stock">Tükendi</option>
                    <option value="inactive">Pasif</option>
                  </select>
                </div>
              )}

              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setItemModal({ open: false, mode: "create", name: "", price: 0, stationCode: "kitchen_main", status: "active" })}
                  className="h-9 px-4 rounded-lg border border-card-border text-xs font-semibold text-muted hover:bg-[#222222] transition-colors"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={isPending}
                  className="h-9 px-4 rounded-lg bg-accent text-background text-xs font-bold hover:bg-accent-hover disabled:opacity-50 transition-colors"
                >
                  {isPending ? "Kaydediliyor..." : "Kaydet"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
