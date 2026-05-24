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
}

export default function CollaborativeCart({ items, onRemove, onClear, onSubmitOrder }: CollaborativeCartProps) {
  const total = items.reduce((acc, item) => acc + item.price * item.quantity, 0);

  return (
    <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-md flex flex-col space-y-6 relative overflow-hidden">
      {/* Glow border background */}
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary to-accent" />

      {/* Header */}
      <div className="flex justify-between items-center pb-4 border-b border-card-border">
        <div>
          <h2 className="font-bold text-lg flex items-center gap-2">
            Kolaboratif Sepet
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-semibold">Masa 12</span>
          </h2>
          <p className="text-muted text-[10px] mt-0.5">Aynı masadaki arkadaşlarınızla ortak sepet</p>
        </div>
        <button 
          onClick={onClear}
          className="text-xs text-muted hover:text-error transition-colors"
          disabled={items.length === 0}
        >
          Temizle
        </button>
      </div>

      {/* Live Active Guests Avatars */}
      <div className="flex items-center gap-2 pb-4 border-b border-card-border">
        <span className="text-[10px] font-bold tracking-wide uppercase text-muted mr-1">Masadakiler:</span>
        <div className="flex -space-x-2">
          <div className="h-6 w-6 rounded-full bg-orange-500 border border-card-bg flex items-center justify-center text-[9px] font-bold text-white" title="Siz">Siz</div>
          <div className="h-6 w-6 rounded-full bg-emerald-500 border border-card-bg flex items-center justify-center text-[9px] font-bold text-white" title="Ahmet">AH</div>
          <div className="h-6 w-6 rounded-full bg-indigo-500 border border-card-bg flex items-center justify-center text-[9px] font-bold text-white" title="Elif">EL</div>
        </div>
        <span className="text-[10px] text-accent font-semibold animate-pulse ml-1">3 kişi bağlı</span>
      </div>

      {/* Cart Items List */}
      {items.length === 0 ? (
        <div className="py-8 text-center space-y-2">
          <p className="text-muted text-sm">Sepetiniz şu an boş.</p>
          <p className="text-[10px] text-muted">Sol taraftaki menüden leziz yemekler eklemeye başlayın.</p>
        </div>
      ) : (
        <div className="divide-y divide-card-border overflow-y-auto max-h-60 pr-1">
          {items.map(item => (
            <div key={item.id} className="py-3 flex justify-between items-start gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm">{item.name}</span>
                  <span className="text-xs text-muted">x{item.quantity}</span>
                </div>
                <div className="flex items-center gap-1.5 text-[9px]">
                  <span className={`h-1.5 w-1.5 rounded-full ${item.avatarColor}`} />
                  <span className="text-muted">{item.addedBy} tarafından eklendi</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-sm text-foreground">₺{item.price * item.quantity}</span>
                <button
                  onClick={() => onRemove(item.id)}
                  className="text-muted hover:text-error text-xs p-1"
                >
                  &times;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cart Total and Order Submission */}
      <div className="pt-4 border-t border-card-border space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-sm font-semibold text-muted">Toplam Tutar:</span>
          <span className="text-xl font-extrabold text-primary">₺{total}</span>
        </div>

        <button
          onClick={onSubmitOrder}
          disabled={items.length === 0}
          className="w-full py-3 rounded-xl bg-primary hover:bg-primary-hover text-background text-sm font-bold shadow-md shadow-primary/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed glow-btn flex items-center justify-center gap-2"
        >
          <span>Siparişi Mutfağa İlet</span>
          <span className="text-xs px-2 py-0.5 rounded bg-background/25 text-background font-bold">₺{total}</span>
        </button>
        <p className="text-center text-[9px] text-muted leading-relaxed">
          Mutfak siparişi hazırlamaya başladığında bildirim alacaksınız.
        </p>
      </div>
    </div>
  );
}
