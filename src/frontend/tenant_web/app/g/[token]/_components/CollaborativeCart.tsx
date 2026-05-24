"use client";

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  addedBy: string;
  avatarColor: string;
}

interface CollaborativeCartProps {
  items: CartItem[];
  onRemove: (id: string) => void;
  onClear: () => void;
  onSubmitOrder: () => void;
  onClose?: () => void;
}

export default function CollaborativeCart({ items, onRemove, onClear, onSubmitOrder, onClose }: CollaborativeCartProps) {
  const total = items.reduce((acc, item) => acc + item.price * item.quantity, 0);

  return (
    <div className="bg-[#1a1a1a] text-[#e8e0d0] p-6 flex flex-col space-y-6 relative overflow-hidden font-sans h-full rounded-t-2xl">
      {/* Top Slide Handle (Premium Sheet Indicator) */}
      <div className="mx-auto h-1.5 w-12 rounded-full bg-[#2e2e2e] mb-2 cursor-pointer" onClick={onClose} />

      {/* Header */}
      <div className="flex justify-between items-center pb-4 border-b border-[#2e2e2e]">
        <div>
          <h2 className="font-playfair font-bold text-lg text-[#c9a84c] flex items-center gap-2">
            Ortak Sepetiniz
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#c9a84c]/10 border border-[#c9a84c]/20 text-[#c9a84c] font-bold">Masa 12</span>
          </h2>
          <p className="text-[#a09070] text-[10px] mt-0.5">Masadaki herkesle aynı anda güncellenir</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={onClear}
            className="text-[10px] uppercase tracking-wider font-bold text-[#a09070] hover:text-[#ef4444] transition-colors"
            disabled={items.length === 0}
          >
            Temizle
          </button>
          {onClose && (
            <button 
              onClick={onClose}
              className="text-xs text-[#a09070] bg-[#222222] border border-[#2e2e2e] rounded-full h-6 w-6 flex items-center justify-center font-bold hover:text-white"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Connected Guests Section */}
      <div className="flex items-center justify-between pb-4 border-b border-[#2e2e2e]">
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-bold tracking-wide uppercase text-[#a09070]">Aktif Bağlantılar:</span>
          <div className="flex -space-x-1.5">
            <div className="h-5 w-5 rounded-full bg-orange-500 border border-[#1a1a1a] flex items-center justify-center text-[8px] font-bold text-white" title="Siz">Siz</div>
            <div className="h-5 w-5 rounded-full bg-emerald-500 border border-[#1a1a1a] flex items-center justify-center text-[8px] font-bold text-white" title="Ahmet">AH</div>
            <div className="h-5 w-5 rounded-full bg-indigo-500 border border-[#1a1a1a] flex items-center justify-center text-[8px] font-bold text-white" title="Elif">EL</div>
          </div>
        </div>
        <span className="text-[9px] text-[#34d399] font-bold flex items-center gap-1 animate-pulse">
          <span className="h-1 w-1 rounded-full bg-[#34d399]" /> Canlı Eşzamanlı
        </span>
      </div>

      {/* Cart Items List */}
      {items.length === 0 ? (
        <div className="flex-1 py-12 flex flex-col items-center justify-center space-y-2 text-center">
          <span className="text-3xl">🍽️</span>
          <p className="text-[#a09070] text-xs font-semibold">Sepetiniz şu an boş.</p>
          <p className="text-[10px] text-[#666]">Leziz içecek ve yemekleri seçerek masanın sepetine ekleyebilirsiniz.</p>
        </div>
      ) : (
        <div className="flex-1 divide-y divide-[#2e2e2e]/50 overflow-y-auto max-h-72 pr-1 scrollbar-none">
          {items.map(item => (
            <div key={item.id} className="py-3.5 flex justify-between items-start gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm text-[#e8e0d0] leading-snug">{item.name}</span>
                  <span className="text-[10px] font-bold text-[#c9a84c] bg-[#c9a84c]/5 border border-[#c9a84c]/20 px-1.5 py-0.2 rounded">x{item.quantity}</span>
                </div>
                <div className="flex items-center gap-1 text-[9px] text-[#a09070]">
                  <span className="h-1 w-1 rounded-full bg-orange-500" />
                  <span>{item.addedBy === "Siz" ? "Siz eklediniz" : `${item.addedBy} ekledi`}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-sm text-[#e8e0d0]">₺{item.price * item.quantity}</span>
                <button
                  onClick={() => onRemove(item.id)}
                  className="text-[#666] hover:text-[#ef4444] text-xs font-bold p-1 transition-colors"
                >
                  &times;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cart Total and Order Submission */}
      <div className="pt-4 border-t border-[#2e2e2e] space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold uppercase tracking-wider text-[#a09070]">Toplam Tutar:</span>
          <span className="font-playfair text-xl font-extrabold text-[#c9a84c]">₺{total}</span>
        </div>

        <button
          onClick={onSubmitOrder}
          disabled={items.length === 0}
          className="w-full py-3.5 rounded-xl bg-[#c9a84c] hover:bg-[#a07832] disabled:bg-[#222] text-[#111111] disabled:text-[#666] text-sm font-bold shadow-lg shadow-[#c9a84c]/10 transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed glow-btn flex items-center justify-center gap-2"
        >
          <span>Siparişi Mutfak Ekibine İlet</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#111111]/15 text-[#111111] font-extrabold">₺{total}</span>
        </button>
        <p className="text-center text-[9px] text-[#666] leading-relaxed">
          Siparişiniz iletildiğinde masa hesabınıza yansıyacak ve hazırlanmaya başlanacaktır.
        </p>
      </div>
    </div>
  );
}
