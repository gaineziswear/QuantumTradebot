// Currency exchange rate utility
let currentUSDToINR = 83; // Default fallback rate

export const fetchUSDToINRRate = async (): Promise<number> => {
  try {
    // Check if we have a recent cached rate (less than 1 hour old)
    const cachedRate = localStorage.getItem('usd_to_inr_rate');
    const cachedTime = localStorage.getItem('usd_to_inr_updated');

    if (cachedRate && cachedTime) {
      const timeDiff = Date.now() - parseInt(cachedTime);
      const oneHour = 60 * 60 * 1000;

      if (timeDiff < oneHour) {
        currentUSDToINR = parseFloat(cachedRate);
        return currentUSDToINR;
      }
    }

    // Try multiple APIs for better reliability
    const apis = [
      'https://api.exchangerate-api.com/v4/latest/USD',
      'https://api.fxratesapi.com/latest?base=USD&symbols=INR',
      'https://open.er-api.com/v6/latest/USD'
    ];

    for (const apiUrl of apis) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

        const response = await fetch(apiUrl, {
          signal: controller.signal,
          headers: {
            'Accept': 'application/json',
            'User-Agent': 'AI-Crypto-Trading-Bot/1.0'
          }
        });

        clearTimeout(timeoutId);

        if (!response.ok) continue;

        const data = await response.json();
        let rate = null;

        // Handle different API response formats
        if (data.rates && data.rates.INR) {
          rate = data.rates.INR;
        } else if (data.rates && data.rates.USD) {
          rate = 1 / data.rates.USD; // Some APIs return inverse rates
        }

        if (rate && rate > 50 && rate < 100) { // Sanity check for INR rate
          currentUSDToINR = rate;
          localStorage.setItem('usd_to_inr_rate', currentUSDToINR.toString());
          localStorage.setItem('usd_to_inr_updated', Date.now().toString());
          console.log(`✅ Exchange rate updated: 1 USD = ₹${currentUSDToINR.toFixed(2)}`);
          return currentUSDToINR;
        }
      } catch (apiError) {
        console.warn(`Exchange rate API failed: ${apiUrl}`, apiError);
        continue; // Try next API
      }
    }

    throw new Error('All exchange rate APIs failed');

  } catch (error) {
    console.warn('Failed to fetch live exchange rate, using fallback');

    // Fallback to cached rate
    const cached = localStorage.getItem('usd_to_inr_rate');
    if (cached && parseFloat(cached) > 50) {
      currentUSDToINR = parseFloat(cached);
      console.log(`Using cached exchange rate: 1 USD = ₹${currentUSDToINR.toFixed(2)}`);
    } else {
      // Final fallback to a reasonable default
      currentUSDToINR = 83; // Conservative fallback rate
      console.log(`Using default exchange rate: 1 USD = ₹${currentUSDToINR.toFixed(2)}`);
    }
  }

  return currentUSDToINR;
};

export const getCurrentUSDToINRRate = (): number => {
  return currentUSDToINR;
};

export const formatINR = (usdAmount: number): string => {
  const inrAmount = usdAmount * currentUSDToINR;
  return `₹${inrAmount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
};

export const formatINRWithDecimals = (usdAmount: number): string => {
  const inrAmount = usdAmount * currentUSDToINR;
  return `₹${inrAmount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

// Initialize exchange rate on module load
fetchUSDToINRRate().catch(() => {
  console.warn('Initial exchange rate fetch failed, using default rate');
});

// Update exchange rate every 5 minutes
setInterval(() => {
  fetchUSDToINRRate().catch(() => {
    console.warn('Periodic exchange rate update failed');
  });
}, 5 * 60 * 1000);
