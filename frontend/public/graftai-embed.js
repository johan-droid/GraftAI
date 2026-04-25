/**
 * GraftAI Official Embed Script
 * Usage: <script src="https://api.graftai.tech/graftai-embed.js" async></script>
 * <div class="graftai-inline-widget" data-url="https://api.graftai.tech/public/username/event"></div>
 */

(function() {
    // Prevent double initialization
    if (window.GraftAIWidget) return;
    window.GraftAIWidget = true;

    function initWidgets() {
        const widgets = document.querySelectorAll('.graftai-inline-widget');
        
        widgets.forEach(widget => {
            if (widget.dataset.initialized) return;
            
            const url = widget.getAttribute('data-url');
            if (!url) {
                console.error("GraftAI: Missing data-url attribute on widget container.");
                return;
            }

            // Create the iframe
            const iframe = document.createElement('iframe');
            
            // Append a query param so the Next.js app knows to render in "Embed Mode" 
            // (e.g., hiding headers/footers)
            const embedUrl = new URL(url);
            embedUrl.searchParams.set('embed', 'true');
            
            iframe.src = embedUrl.toString();
            iframe.width = '100%';
            iframe.height = '100%';
            iframe.frameBorder = '0';
            iframe.style.minHeight = '650px'; // Safe minimum for booking flow
            iframe.style.border = 'none';
            iframe.style.borderRadius = '8px';
            iframe.style.boxShadow = '0 4px 20px rgba(0,0,0,0.05)';

            widget.style.position = 'relative';
            widget.style.width = '100%';
            widget.style.height = '100%';
            widget.appendChild(iframe);
            
            widget.dataset.initialized = 'true';
        });
    }

    // Listen for events from the Next.js booking app (Cross-Origin)
    window.addEventListener('message', function(e) {
        const trustedOrigin = document.referrer
            ? new URL(document.referrer).origin
            : null;

        if (!trustedOrigin || e.origin !== trustedOrigin) {
            return;
        }

        if (e.data && e.data.type === 'graftai:booking_complete') {
            console.log("GraftAI Booking Completed:", e.data.payload);
            if (typeof window.onGraftAIBookingComplete === 'function') {
                window.onGraftAIBookingComplete(e.data.payload);
            }
        }
    });

    // Auto-init on script load
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        initWidgets();
    } else {
        document.addEventListener('DOMContentLoaded', initWidgets);
    }
})();
