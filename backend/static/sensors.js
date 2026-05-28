const SensorManager = {
    startSensors(logCallback) {
        // 1. Visibility API (Switch tab, minimize app)
        document.addEventListener("visibilitychange", () => {
            if (document.visibilityState === 'hidden') {
                logCallback("BROWSER_BACKGROUNDED", "Peserta meminimalkan browser atau beralih tab");
            }
        });

        // 2. Focus/Blur (Notification drawer pulled down, lost focus)
        window.addEventListener("blur", () => {
            // Debounce slightly to prevent false positive from fast touch interactions
            setTimeout(() => {
                if (!document.hasFocus()) {
                    logCallback("FOCUS_LOST", "Browser kehilangan fokus layar utama");
                }
            }, 500);
        });

        // 3. Screen Constraints (Detect split screen / unexpected resize)
        let initialHeight = window.innerHeight;
        window.addEventListener('resize', () => {
            const heightChangeRatio = Math.abs(window.innerHeight - initialHeight) / initialHeight;
            // If height changes by more than 30%, it might be a split screen activation
            if (heightChangeRatio > 0.3) {
                logCallback("SCREEN_CONSTRAINT_VIOLATION", "Dimensi layar berubah drastis, kemungkinan Split Screen");
                initialHeight = window.innerHeight; // reset
            }
        });
    }
};
